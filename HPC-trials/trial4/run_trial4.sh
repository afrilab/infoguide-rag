#!/bin/bash
#SBATCH --job-name=mnist_gpu_test
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:tesla_v100:1
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err

mkdir -p logs

echo "Job started at $(date)"
echo "Node: $(hostname)"
nvidia-smi
echo "-----"

module load python/3.12.9

pip install -r requirements.txt

# GPU ile kısa eğitim (çok kısa tuttuk)
python main.py --epochs 1 --batch-size 64

echo "Job finished"
