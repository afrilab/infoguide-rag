#!/bin/bash
#SBATCH --job-name=install-vllm
#SBATCH --output=/cta/users/teoman.arabul/finsage/logs/install-vllm-%j.out
#SBATCH --error=/cta/users/teoman.arabul/finsage/logs/install-vllm-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1

set -euo pipefail

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "[INFO] Started at $(date)"
"$ENV_PY" -m pip install vllm
"$ENV_PY" -m pip show vllm
echo "[INFO] Finished at $(date)"
