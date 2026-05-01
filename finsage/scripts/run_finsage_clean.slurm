#!/bin/bash
#SBATCH --job-name=finsage-run
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/finsage-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/finsage-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1

set -euo pipefail

PROJECT_DIR="/cta/users/teoman.arabul/finsage"
ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"
CONFIG_PATH="$PROJECT_DIR/config/production.yaml"

mkdir -p "$PROJECT_DIR/logs"

echo "[INFO] Job started at $(date)"
echo "[INFO] Node: $(hostname)"
echo "[INFO] Python: $ENV_PY"
nvidia-smi || true
echo "-----"

readarray -t CFG < <(
"$ENV_PY" - <<'PY' "$CONFIG_PATH"
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

LLM_HOST="$("$ENV_PY" - <<'PY' "$LLM_BASE_URL"
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print(u.hostname or "127.0.0.1")
PY
)"

LLM_PORT="$("$ENV_PY" - <<'PY' "$LLM_BASE_URL"
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print(u.port or 8000)
PY
)"

echo "[INFO] Model: $MODEL_NAME"
echo "[INFO] vLLM endpoint: http://$LLM_HOST:$LLM_PORT/v1"

cd "$PROJECT_DIR"

cleanup() {
  if [[ -n "${VLLM_PID:-}" ]] && kill -0 "$VLLM_PID" 2>/dev/null; then
    echo "[INFO] Stopping vLLM"
    kill -INT "$VLLM_PID" || true
  fi
}
trap cleanup EXIT INT TERM

"$ENV_PY" -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_NAME" \
  --host "$LLM_HOST" \
  --port "$LLM_PORT" \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  > "$PROJECT_DIR/logs/vllm-${SLURM_JOB_ID}.log" 2>&1 &

VLLM_PID=$!

echo "[INFO] Waiting for vLLM..."
for _ in $(seq 1 180); do
  if curl -sf "http://$LLM_HOST:$LLM_PORT/v1/models" >/dev/null; then
    echo "[INFO] vLLM is ready"
    break
  fi
  sleep 2
done

if ! curl -sf "http://$LLM_HOST:$LLM_PORT/v1/models" >/dev/null; then
  echo "[ERROR] vLLM did not become ready in time"
  exit 1
fi

export CONFIG_PATH
cd "$PROJECT_DIR/src"

PYTHONPATH="$PROJECT_DIR/src" exec "$ENV_PY" -m gunicorn -w 1 -b 0.0.0.0:6005 --timeout 180 server:app
