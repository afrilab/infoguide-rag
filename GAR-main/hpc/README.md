# HPC Scripts (Sabancı Tosun)

Scripts for Sabancı University Tosun cluster. **Ready for submission; not auto-submitted.**

## Data layout (HPC reproducibility)
```
data/
├── raw/           # dataset.csv
├── processed/     # pipeline outputs
└── benchmarks/    # Markdown/, {Task}_qrels.tsv
```

## setup.sh
Creates venv, installs `requirements.txt`. Run once after upload.
```bash
cd GAR-main
bash hpc/setup.sh
```

## run_cpu.sh
SLURM script for main pipeline (Selection → DPO → Finetuning → Finetuned DPO). Uses `short_mdbf` partition.
```bash
sbatch hpc/run_cpu.sh
```

## run_gpu.sh
Embedder fine-tuning. Uses `cuda` partition.
```bash
sbatch hpc/run_gpu.sh
```

## run_gpu_hybrid.sh
Hybrid search (BM25 + dense + rerank). Uses `cuda` partition.
```bash
sbatch hpc/run_gpu_hybrid.sh
```

## Partitions
- CPU: `short_mdbf` / qos `short_mdbf` / account `mdbf`
- GPU: `cuda` / qos `cuda` / account `cuda`

## Env
Scripts source `.env` when present. Set `OPENAI_API_KEY`, `HUGGINGFACE_API_KEY`, `HF_TOKEN`, `repo_id`, `repo_owner`.

## Before Running
1. Dataset: `data/raw/dataset.csv` (main pipeline)
2. Finetuning: `data/benchmarks/Markdown/{Task}/`, `data/benchmarks/{Task}_qrels.tsv` (fallback: project root)
3. `OPENAI_API_KEY`, `HUGGINGFACE_API_KEY` (or `HF_TOKEN`), `repo_id`, `repo_owner` in `.env`
4. `flash-attn` may fail on login node; run setup on GPU node if needed

## Outputs
- `logs/job_<id>.out`, `logs/job_<id>.err`
- Main: `data/processed/*.csv`, `outputs/`
- Hybrid search: `outputs/hybrid_search/`
- Finetuning: `outputs/fine-tuned-model/`
