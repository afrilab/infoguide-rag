#!/bin/bash
#SBATCH --job-name=prime_test
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

mkdir -p logs

echo "Job started at $(date)"
echo "Node: $(hostname)"
echo "-----"

module load python/3.12.9

python prime_test.py

echo "-----"
echo "Job finished at $(date)"
