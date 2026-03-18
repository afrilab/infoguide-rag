#!/bin/bash
#SBATCH --job-name=simple_python_job
#SBATCH --output=logs/job_%j.out
#SBATCH --error=logs/job_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
mkdir -p logs
mkdir -p outputs
python3 simple_hpc_job.py
