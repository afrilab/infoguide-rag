#!/bin/bash
#SBATCH --job-name=build-chroma-cpu
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/build-chroma-cpu-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/build-chroma-cpu-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00

set -euo pipefail

mkdir -p /cta/users/teoman.arabul/finsage/logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "[INFO] Started at $(date)"
echo "[INFO] Node: $(hostname)"
echo "[INFO] Python: $ENV_PY"

"$ENV_PY" /cta/users/teoman.arabul/finsage/scripts/build_chroma.py

echo "[INFO] Finished at $(date)"
