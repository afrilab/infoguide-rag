#!/bin/bash
#SBATCH --job-name=build-chroma-ts
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/build-chroma-ts-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/build-chroma-ts-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
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

"$ENV_PY" "$PROJECT_DIR/scripts/build_chroma_and_ts.py"

echo "[INFO] Finished at $(date)"
