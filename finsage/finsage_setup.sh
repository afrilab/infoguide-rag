#!/bin/bash
#SBATCH --job-name=finsage-setup
#SBATCH --output=logs/setup-%j.out
#SBATCH --error=logs/setup-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

set -euo pipefail
mkdir -p logs

module load conda/miniconda_20250420
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate finsage

export PYTHONNOUSERSITE=1
export PIP_NO_USER=1

python -m pip install --upgrade pip

echo "=== Installing core ML stack ==="
python -m pip install \
    torch \
    "transformers==4.41.2" \
    "huggingface-hub>=0.23,<1.0" \
    sentence-transformers \
    FlagEmbedding \
    accelerate

echo "=== Installing LangChain stack ==="
python -m pip install \
    langchain \
    langchain-community \
    langchain-core \
    langchain-chroma \
    langchain-huggingface

echo "=== Installing retrieval backends ==="
python -m pip install \
    faiss-cpu \
    bm25s \
    PyStemmer \
    chromadb

echo "=== Installing API + server ==="
python -m pip install \
    flask \
    flask-cors \
    gunicorn \
    openai \
    requests

echo "=== Installing data + eval utilities ==="
python -m pip install \
    pyyaml \
    pandas \
    numpy \
    tqdm \
    matplotlib \
    GPUtil \
    pytrec_eval

echo "=== Installed versions ==="
python -m pip list | grep -E \
    "torch|transformers|huggingface|langchain|sentence|Flag|faiss|bm25s|chromadb|flask|openai|pyyaml|pandas|tqdm|matplotlib|GPUtil" \
    || true

echo "=== Import sanity check ==="
python -c "
import torch; print('torch ok:', torch.__version__)
import transformers; print('transformers ok:', transformers.__version__)
import langchain_huggingface; print('langchain_huggingface ok')
import langchain_chroma; print('langchain_chroma ok')
import bm25s; print('bm25s ok')
import Stemmer; print('PyStemmer ok')
from FlagEmbedding import FlagLLMReranker; print('FlagEmbedding ok')
import faiss; print('faiss ok')
print('All imports passed.')
"

echo "Setup complete."
