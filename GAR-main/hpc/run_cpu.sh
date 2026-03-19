#!/bin/bash
#SBATCH --job-name=gar_cpu
#SBATCH --output=logs/job_%j.out
#SBATCH --error=logs/job_%j.err
#SBATCH --partition=short_mdbf
#SBATCH --qos=short_mdbf
#SBATCH --account=mdbf
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

set -euo pipefail
PROJECT_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$PROJECT_ROOT"

mkdir -p logs outputs
source venv/bin/activate
[ -f .env ] && set -a && source .env && set +a

export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/GAR"
python GAR/main.py
