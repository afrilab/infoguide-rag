#!/bin/bash
#SBATCH --job-name=financerag_resume
#SBATCH --account=users
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=72:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:1
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

set -e
ulimit -s unlimited
echo "Resume job started at $(date)"
echo "Running on node: $(hostname)"
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi || true
echo "---"
module load python/3.12.9

module load sqlite/3.46.0-36f2sjv
export LD_PRELOAD=/cta/apps/opt/spack/linux-ubuntu24.04-x86_64/gcc-13.3.0/sqlite-3.46.0-36f2sjv/lib/libsqlite3.so.0
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"

export PATH="$HOME/.local/bin:$PATH"

echo "HOST: $(hostname)"
echo "PWD: $(pwd)"
echo "PATH: $PATH"

which python3 || true
python3 --version || true
# FinDER failed here before, so rerun with smaller batch size
python rerank.py --task FinDER --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 1 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results

# Remaining final rerank steps
python rerank.py --task ConvFinQA --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 1 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task FinQA --model Alibaba-NLP/gte-multilingual-reranker-base --top_k 200 --batch_size 1 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task TATQA --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 1 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task MultiHiertt --model jinaai/jina-reranker-v2-base-multilingual --top_k 200 --batch_size 32 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results

# Final merge
python rerank.py --save_dir ./results --dataset_dir ./dataset --do_post_process

echo "---"
echo "Resume job finished at $(date)"
