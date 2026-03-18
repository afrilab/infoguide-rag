#!/bin/bash
#SBATCH --job-name=test_job
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --time=00:05:00
#SBATCH --partition=short_mdbf
#SBATCH --qos=short_mdbf
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G

mkdir -p logs
mkdir -p outputs

echo "Job başladı"
hostname

python3 simple_hpc_job.py

echo "Job bitti"
