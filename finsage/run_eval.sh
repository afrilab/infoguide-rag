#!/bin/bash
#SBATCH --job-name=finsage-eval
#SBATCH --output=logs/eval-%j.out
#SBATCH --error=logs/eval-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:1

# =================================================================
# FinSage evaluation pipeline — SLURM submission wrapper
# =================================================================
#
# Submit from the finsage/ directory:
#   sbatch run_eval.sh
#
# What it runs:
#   For each HyDE checkpoint:
#     step1 — HyDE hypothetical-document generation (VLLM + LoRA)
#     step2 — Retrieval evaluation: Recall / Precision / F1
#     step3 — Answer quality:  Faithfulness / Evidence Grounding /
#              Answer Relevance / Hallucination Rate / Verdict
#
# Edit the paths in experiments/retriever/eval_all_retrieval.sh
# before submitting.

set -euo pipefail
mkdir -p logs

echo "========================================"
echo " FinSage Evaluation Job"
echo "========================================"
echo " Start  : $(date)"
echo " Host   : $(hostname)"
echo " GPU    : $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null \
               | head -1 || echo 'N/A')"
echo "========================================"
echo ""

module load conda/miniconda_20250420 2>/dev/null || true
source "$(conda info --base)/etc/profile.d/conda.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/experiments/retriever"

bash eval_all_retrieval.sh

echo ""
echo "========================================"
echo " Evaluation complete: $(date)"
echo "========================================"
