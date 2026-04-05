#!/bin/bash
#!/bin/bash
#SBATCH --job-name=financerag
#SBATCH --account=users
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=72:00:00
#SBATCH --partition=cuda
#SBATCH --qos=cuda
#SBATCH --gres=gpu:1
#SBATCH --output=logs/merge_%j.out
#SBATCH --error=logs/merge_%j.err

set -e
ulimit -s unlimited
echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "---"

module load python/3.12.9
pip install pandas openpyxl

python merge_results_to_excel.py

echo "---"
echo "Job finished at $(date)"
