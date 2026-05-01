#!/bin/bash
#SBATCH --job-name=create-env
#SBATCH --output=logs/create-env-%j.out
#SBATCH --error=logs/create-env-%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda

mkdir -p logs

module load conda/miniconda_20250420
source $(conda info --base)/etc/profile.d/conda.sh

echo "Starting env creation at $(date)"
conda create --prefix /cta/users/teoman.arabul/.conda/envs/finsage_clean python=3.12 -y
echo "Finished env creation at $(date)"
