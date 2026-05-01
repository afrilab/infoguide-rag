#!/bin/bash
#SBATCH --job-name=finsage-clean-setup
#SBATCH --output=logs/setup-clean-%j.out
#SBATCH --error=logs/setup-clean-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

mkdir -p logs

ENV_PY="/cta/users/teoman.arabul/.conda/envs/finsage_clean/bin/python"

echo "Using Python: $ENV_PY"
"$ENV_PY" -m pip --version

echo "Installing core stack..."
"$ENV_PY" -m pip install --upgrade pip
"$ENV_PY" -m pip install torch transformers==4.37.2
"$ENV_PY" -m pip install langchain langchain-community langchain-core langchain-huggingface
"$ENV_PY" -m pip install flask flask-cors requests gunicorn
"$ENV_PY" -m pip install sentence-transformers faiss-cpu

echo "Setup finished."
