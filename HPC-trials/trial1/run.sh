#!/bin/bash
#SBATCH --job-name=model.py
#SBATCH --account=users
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=long_mdbf
#SBATCH --partition=long_mdbf
#SBATCH --time=05:00
#SBATCH --output=logs/%j.out






ulimit -s unlimited

echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "---"

module load python/3.12.9        # check with: module avail python

python model.py

echo "---"
echo "Job finished at $(date)"
