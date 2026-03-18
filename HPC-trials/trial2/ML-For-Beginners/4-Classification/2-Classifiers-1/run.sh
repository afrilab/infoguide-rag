#!/bin/bash
#SBATCH --job-name=simple_hpc_job
#SBATCH --account=users
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=long_mdbf
#SBATCH --partition=long_mdbf
#SBATCH --time=05:00:00
#SBATCH --output=/cta/users/zeynep.deniz/ML-For-Beginners/4-Classification/2-Classifiers-1/logs/%j.out

ulimit -s unlimited

echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "---"

module load python/3.12.9

cd /cta/users/zeynep.deniz/ML-For-Beginners/4-Classification/2-Classifiers-1/

python simple_hpc_job.py

echo "---"
echo "Job finished at $(date)"
