#!/bin/bash
#SBATCH --job-name=gar_gpu_hybrid
#SBATCH --output=logs/job_%j.out
#SBATCH --error=logs/job_%j.err
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --account=cuda
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G

set -euo pipefail
PROJECT_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$PROJECT_ROOT"

mkdir -p logs outputs
source venv/bin/activate
[ -f .env ] && set -a && source .env && set +a

export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/GAR"
python GAR/run_hybrid_search.py
