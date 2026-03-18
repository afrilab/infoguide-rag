#!/bin/bash
#SBATCH --job-name=financerag
#SBATCH --account=users
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=long_mdbf
#SBATCH --partition=long_mdbf
#SBATCH --time=12:00:00
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
set -e
ulimit -s unlimited

echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "---"

module load python/3.12.9
# Install packages
# pip uninstall -y transformer-engine # Use this if flash-attn is not installed
pip install -r requirements.txt
MAX_JOBS=4 pip install flash-attn --no-build-isolation

# Download dataset from kaggle 
python prepare_dataset.py

# Pre-trieval
python pre_retrieval.py

# Intermediate Retrieve
python rerank.py --task FinanceBench --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task FinQABench --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task FinDER --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task ConvFinQA --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task FinQA --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task TATQA --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200
python rerank.py --task MultiHiertt --model jinaai/jina-reranker-v2-base-multilingual --top_k 99999 --batch_size 128 --dataset_dir ./dataset --dataset_filename merge.json --save_dir ./results/intermediate --save_top_k 200

# Final Retrieve
python rerank.py --task FinanceBench --model jinaai/jina-reranker-v2-base-multilingual --top_k 200 --batch_size 128 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task FinQABench --model jinaai/jina-reranker-v2-base-multilingual --top_k 200 --batch_size 128 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task FinDER --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 4 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task ConvFinQA --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 4 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task FinQA --model Alibaba-NLP/gte-multilingual-reranker-base  --top_k 200 --batch_size 4 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task TATQA --model BAAI/bge-reranker-v2-m3 --top_k 200 --batch_size 4 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --task MultiHiertt --model jinaai/jina-reranker-v2-base-multilingual --top_k 200 --batch_size 128 --dataset_dir ./results/intermediate --dataset_filename results.json --save_dir ./results
python rerank.py --save_dir ./results --dataset_dir ./dataset --do_post_process

echo "---"
echo "Job finished at $(date)"
