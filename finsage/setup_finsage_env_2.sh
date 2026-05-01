#!/bin/bash
#SBATCH --job-name=finsage-setup2
#SBATCH --output=logs/setup2-%j.out
#SBATCH --error=logs/setup2-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

mkdir -p logs

module load conda/miniconda_20250420
source $(conda info --base)/etc/profile.d/conda.sh
conda activate finsage

export PYTHONNOUSERSITE=1
export PIP_NO_USER=1

python -m pip install --upgrade pip

python -m pip install torch transformers langchain-huggingface
python -m pip install FlagEmbedding
