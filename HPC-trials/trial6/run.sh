#!/bin/bash
#SBATCH --job-name=basic_test
#SBATCH --output=logs/job_%j.out
#SBATCH --error=logs/job_%j.err
#SBATCH --partition=short_mdbf
#SBATCH --qos=short_mdbf
#SBATCH --account=mdbf
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=1G

mkdir -p logs
mkdir -p outputs

python3 simple_hpc_job.py
