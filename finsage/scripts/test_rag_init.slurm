#!/bin/bash
#SBATCH --job-name=test-rag-init
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/test-rag-init-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/test-rag-init-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1

set -euo pipefail

mkdir -p /cta/users/teoman.arabul/finsage/logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"
PROJECT_DIR="/cta/users/teoman.arabul/finsage"

echo "[INFO] Started at $(date)"
echo "[INFO] Node: $(hostname)"
echo "[INFO] Python: $ENV_PY"
nvidia-smi || true

cd "$PROJECT_DIR"

PYTHONPATH="$PROJECT_DIR/src" \
"$ENV_PY" "$PROJECT_DIR/scripts/test_rag_init.py"

echo "[INFO] Finished at $(date)"
