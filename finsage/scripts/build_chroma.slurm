#!/bin/bash
#SBATCH --job-name=build-chroma
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/build-chroma-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/build-chroma-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1

set -euo pipefail

mkdir -p /cta/users/teoman.arabul/finsage/logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "[INFO] Started at $(date)"
echo "[INFO] Node: $(hostname)"
echo "[INFO] Python: $ENV_PY"

nvidia-smi || true

"$ENV_PY" /cta/users/teoman.arabul/finsage/scripts/build_chroma.py

echo "[INFO] Finished at $(date)"
