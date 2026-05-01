#!/bin/bash
#SBATCH --job-name=install-flag
#SBATCH --output=logs/install-flag-%j.out
#SBATCH --error=logs/install-flag-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

set -euo pipefail

mkdir -p logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "Using Python: $ENV_PY"
"$ENV_PY" -m pip install FlagEmbedding
"$ENV_PY" -m pip show FlagEmbedding
