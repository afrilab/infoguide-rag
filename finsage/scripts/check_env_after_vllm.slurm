#!/bin/bash
#SBATCH --job-name=check-env
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/check-env-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/check-env-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1

set -euo pipefail

PROJECT_DIR="/cta/users/teoman.arabul/finsage"
ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

mkdir -p "$PROJECT_DIR/logs"

echo "[INFO] Started at $(date)"
echo "[INFO] Node: $(hostname)"
echo "[INFO] Python: $ENV_PY"

"$ENV_PY" -m pip show vllm || true

cd "$PROJECT_DIR"

echo "[INFO] Checking RAGManager import..."
PYTHONPATH="$PROJECT_DIR/src" \
"$ENV_PY" -c "from utils.ragManager import RAGManager; print('rag ok')"

echo "[INFO] Checking ChatService import..."
PYTHONPATH="$PROJECT_DIR/src" \
"$ENV_PY" -c "from utils.vllmChatService import ChatService; print('chat ok')"

echo "[INFO] Checking numpy/langchain versions..."
PYTHONPATH="$PROJECT_DIR/src" \
"$ENV_PY" -c "import numpy, langchain, langchain_community; print('numpy=', numpy.__version__); print('langchain=', langchain.__version__); print('langchain_community=', langchain_community.__version__)"

echo "[INFO] Finished at $(date)"
