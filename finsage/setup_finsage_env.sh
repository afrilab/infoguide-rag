#!/bin/bash
#SBATCH --job-name=finsage-setup
#SBATCH --output=logs/setup-%j.out
#SBATCH --error=logs/setup-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

mkdir -p logs

module load conda/miniconda_20250420
source $(conda info --base)/etc/profile.d/conda.sh
conda activate finsage

pip install torch transformers vllm openai \
sentence-transformers \
langchain langchain-community langchain-core langchain-chroma langchain-huggingface \
faiss-cpu
