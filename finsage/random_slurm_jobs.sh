#!/bin/bash
#SBATCH --job-name=finsage-clean-fix
#SBATCH --output=logs/setup-fix-%j.out
#SBATCH --error=logs/setup-fix-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

set -euo pipefail

mkdir -p logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "Starting setup fix at $(date)"
echo "Using Python: $ENV_PY"

"$ENV_PY" -c "import sys; print(sys.executable)"
"$ENV_PY" -m pip --version

echo "Upgrading pip..."
"$ENV_PY" -m pip install --upgrade pip

echo "Installing stable core stack..."
"$ENV_PY" -m pip install --upgrade \
  "transformers==4.41.2" \
  "huggingface-hub>=0.23,<1.0"

echo "Installing project dependencies..."
"$ENV_PY" -m pip install --upgrade \
  torch \
  langchain \
  langchain-community \
  langchain-core \
  langchain-huggingface \
  flask \
  flask-cors \
  requests \
  gunicorn \
  sentence-transformers \
  faiss-cpu \
  pyyaml

echo "Installed versions:"
"$ENV_PY" -m pip list | grep -E "torch|transformers|huggingface|langchain|sentence-transformers|faiss|flask|gunicorn|PyYAML" || true

echo "Running import checks..."
cd /cta/users/teoman.arabul/finsage/src

"$ENV_PY" -c "import torch; print('torch ok')"
"$ENV_PY" -c "import transformers; print('transformers ok')"
"$ENV_PY" -c "import langchain_huggingface; print('langchain_huggingface ok')"
"$ENV_PY" -c "from utils.ragManager import RAGManager; print('rag ok')"

echo "Setup fix finished at $(date)"
