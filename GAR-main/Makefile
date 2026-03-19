.PHONY: setup cpu gpu gpu-hybrid pipeline

setup:
	bash hpc/setup.sh

cpu:
	sbatch hpc/run_cpu.sh

gpu:
	sbatch hpc/run_gpu.sh

gpu-hybrid:
	sbatch hpc/run_gpu_hybrid.sh

pipeline: setup cpu
