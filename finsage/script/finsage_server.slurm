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

PROJECT_DIR="${PROJECT_DIR:-$SLURM_SUBMIT_DIR}"
PRODUCTION_CONFIG="$PROJECT_DIR/config/production.yaml"
EXAMPLE_CONFIG="$PROJECT_DIR/config/example.yaml"

if [[ -z "${CONFIG_PATH:-}" ]]; then
  if [[ -f "$PRODUCTION_CONFIG" ]]; then
    CONFIG_PATH="$PRODUCTION_CONFIG"
  elif [[ -f "$EXAMPLE_CONFIG" ]]; then
    CONFIG_PATH="$EXAMPLE_CONFIG"
  else
    echo "[ERROR] No config file found. Expected one of:"
    echo "        $PRODUCTION_CONFIG"
    echo "        $EXAMPLE_CONFIG"
    exit 1
  fi
fi

VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.90}"
VLLM_TP_SIZE="${VLLM_TP_SIZE:-1}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
CONDA_ENV="${CONDA_ENV:-}"
CONDA_SH="${CONDA_SH:-}"
MODULES="${MODULES:-}"

mkdir -p "$PROJECT_DIR/logs"

if [[ -n "$MODULES" ]]; then
  for module_name in $MODULES; do
    module load "$module_name"
  done
fi

if [[ -n "$CONDA_ENV" ]]; then
  if [[ -z "$CONDA_SH" ]]; then
    if command -v conda >/dev/null 2>&1; then
      CONDA_SH="$(dirname "$(dirname "$(command -v conda)")")/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
      CONDA_SH="$HOME/miniconda3/etc/profile.d/conda.sh"
    fi
  fi

  if [[ -z "$CONDA_SH" || ! -f "$CONDA_SH" ]]; then
    echo "[ERROR] Conda init script not found. Set CONDA_SH=/path/to/conda.sh"
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$CONDA_SH"
  conda activate "$CONDA_ENV"
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
fi

for required_cmd in "$PYTHON_BIN" curl vllm gunicorn; do
  if ! command -v "$required_cmd" >/dev/null 2>&1; then
    echo "[ERROR] Required command not found: $required_cmd"
    exit 1
  fi
done

readarray -t CFG < <(
"$PYTHON_BIN" - <<'PY' "$CONFIG_PATH"
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

LLM_HOST="$("$PYTHON_BIN" - <<'PY' "$LLM_BASE_URL"
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print(u.hostname or "127.0.0.1")
PY
)"

LLM_PORT="$("$PYTHON_BIN" - <<'PY' "$LLM_BASE_URL"
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
if [[ -n "$CONDA_ENV" ]]; then
  echo "[INFO] Conda:   $CONDA_ENV"
fi
if [[ -n "$MODULES" ]]; then
  echo "[INFO] Modules: $MODULES"
fi

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
