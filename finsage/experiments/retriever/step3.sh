#!/bin/bash

# =================================================================
# Step 3: Answer generation + LLM-judge quality evaluation
# =================================================================
#
# Reads result_2.json (step2 output), generates an answer for each
# question from the retrieved context, then scores each answer with
# an LLM judge on faithfulness, evidence grounding, answer relevance,
# hallucination rate, and a PASS / PARTIAL / FAIL verdict.
#
# See step3.py for full input / output format.
#
# Usage (standalone):
#   bash step3.sh <result_2.json> <output_dir> [model] [api_key] [base_url]
#
# Usage (called from eval_all_retrieval.sh):
#   bash step3.sh "${OUT_DIR}/${lora_name}/faiss/result_2.json" \
#                 "${OUT_DIR}/${lora_name}/faiss" \
#                 "${JUDGE_MODEL}" "${JUDGE_API_KEY}" "http://localhost:8001/v1"

activate_conda_env() {
    local env=$1
    echo "Activating conda environment: $env"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda deactivate 2>/dev/null || true
    conda activate "$env" || { echo "ERROR: failed to activate conda env '$env'"; exit 1; }
}

echo "=== Running step3 ==="

input_file=${1:?"Error: input_file (arg 1) is required"}
output_dir=${2:?"Error: output_dir (arg 2) is required"}
model_name=${3:-"judge"}
api_key=${4:-"EMPTY"}
base_url=${5:-"http://localhost:8001/v1"}

[ ! -f "$input_file" ] && { echo "Error: input file not found: $input_file"; exit 1; }

mkdir -p "$output_dir"

activate_conda_env "${ENV_NAME:-finsage}"

echo "Input:      $input_file"
echo "Output dir: $output_dir"
echo "Model:      $model_name  @  $base_url"

python step3.py \
    --input      "$input_file"  \
    --output     "$output_dir"  \
    --model_name "$model_name"  \
    --api_key    "$api_key"     \
    --base_url   "$base_url"

echo "=== Step3 complete — results in: ${output_dir}/result_3.json ==="
