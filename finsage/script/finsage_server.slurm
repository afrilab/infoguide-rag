#!/bin/bash
#SBATCH --job-name=finsage-server
#SBATCH --output=logs/finsage-%j.out
#SBATCH --error=logs/finsage-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:tesla_v100:1
#SBATCH --time=24:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

set -euo pipefail

# Optional: load your cluster modules here
# module load cuda/12.1
# module load gcc/11

# Optional: activate your conda environment
# source "$HOME/miniconda3/etc/profile.d/conda.sh"
# conda activate finsage

PROJECT_DIR="${PROJECT_DIR:-$SLURM_SUBMIT_DIR}"
CONFIG_PATH="${CONFIG_PATH:-$PROJECT_DIR/config/production.yaml}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.90}"
VLLM_TP_SIZE="${VLLM_TP_SIZE:-1}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"

mkdir -p "$PROJECT_DIR/logs"

readarray -t CFG < <(
python - <<'PY' "$CONFIG_PATH"
import sys, yaml
cfg_path = sys.argv[1]
with open(cfg_path, "r", encoding="utf-8") as f:
    c = yaml.safe_load(f)
print(c["llm_model_name"])
print(c["llm_base_url"])
PY
)

MODEL_NAME="${CFG[0]}"
LLM_BASE_URL="${CFG[1]}"

LLM_HOST="$(python - <<'PY' "$LLM_BASE_URL"
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print(u.hostname or "127.0.0.1")
PY
)"

LLM_PORT="$(python - <<'PY' "$LLM_BASE_URL"
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print(u.port or 8000)
PY
)"

echo "[INFO] Project: $PROJECT_DIR"
echo "[INFO] Config:  $CONFIG_PATH"
echo "[INFO] Model:   $MODEL_NAME"
echo "[INFO] vLLM:    http://$LLM_HOST:$LLM_PORT/v1"

cd "$PROJECT_DIR"

cleanup() {
  if [[ -n "${VLLM_PID:-}" ]] && kill -0 "$VLLM_PID" 2>/dev/null; then
    echo "[INFO] Stopping vLLM (PID: $VLLM_PID)"
    kill -INT "$VLLM_PID" || true
  fi
}
trap cleanup EXIT INT TERM

vllm serve "$MODEL_NAME" \
  --host "$LLM_HOST" \
  --port "$LLM_PORT" \
  --tensor-parallel-size "$VLLM_TP_SIZE" \
  --gpu-memory-utilization "$VLLM_GPU_MEMORY_UTILIZATION" \
  > "$PROJECT_DIR/logs/vllm-${SLURM_JOB_ID}.log" 2>&1 &
VLLM_PID=$!

echo "[INFO] Waiting for vLLM to be ready..."
for _ in $(seq 1 180); do
  if curl -sf "http://$LLM_HOST:$LLM_PORT/v1/models" >/dev/null; then
    echo "[INFO] vLLM is ready."
    break
  fi
  sleep 2
done

if ! curl -sf "http://$LLM_HOST:$LLM_PORT/v1/models" >/dev/null; then
  echo "[ERROR] vLLM did not become ready in time."
  exit 1
fi

export CONFIG_PATH
cd "$PROJECT_DIR/src"
exec gunicorn -w "$GUNICORN_WORKERS" -b 0.0.0.0:6005 --timeout 180 server:app
