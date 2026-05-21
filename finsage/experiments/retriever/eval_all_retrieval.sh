#!/bin/bash

# =================================================================
# Evaluate all trained HyDE models across checkpoints
# =================================================================
#
# Pipeline: step1 (HyDE generation) → step2 (retrieval metrics) → step3 (answer quality)
# Submit to HPC:  sbatch ../../run_eval.sh
# Run directly:   bash eval_all_retrieval.sh

# ── CONFIGURE THESE FOR YOUR CLUSTER ─────────────────────────────
FINSAGE_ROOT="/cta/users/${USER}/finsage"

OUT_DIR="${FINSAGE_ROOT}/experiments/retriever/expand"
EVAL_DIR="${FINSAGE_ROOT}/experiments/retriever"
ANSWER_FILE="${EVAL_DIR}/answer/75_testingset_75updated_mul.json"

# HyDE model: LoRA-fine-tuned Qwen2.5-7B
MODEL_PATH="${FINSAGE_ROOT}/models/Qwen2.5-7B-Instruct"
MODEL="Qwen2___5-7B-Instruct"
ADAPTER_PATH="${FINSAGE_ROOT}/models/lora/hyde3_epoch3"
VLLM_PORT=8000

# Judge LLM used in step3 for answer generation and quality evaluation.
# Set JUDGE_MODEL_PATH="" to skip step3 entirely.
JUDGE_MODEL_PATH="${FINSAGE_ROOT}/models/Qwen2.5-72B-Instruct-AWQ"
JUDGE_MODEL="Qwen/Qwen2___5-72B-Instruct-AWQ"
JUDGE_API_KEY="EMPTY"
JUDGE_PORT=8001

# Conda environment that has all finsage dependencies installed
ENV_NAME="finsage"
# ─────────────────────────────────────────────────────────────────

MAX_LENGTH=16000
CHECKPOINT_LIST=("checkpoint-200" "checkpoint-400" "checkpoint-600" "checkpoint-800" "checkpoint-843")

# ── Helpers ──────────────────────────────────────────────────────

activate_conda_env() {
    local env=$1
    echo "Activating conda environment: $env"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda deactivate 2>/dev/null || true
    conda activate "$env" || { echo "ERROR: failed to activate conda env '$env'"; exit 1; }
}

wait_for_server() {
    local port=$1
    local max_attempts=${2:-60}
    local attempt=1
    echo "Waiting for VLLM server on port $port..."
    while ! curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: server on port $port did not start after $max_attempts attempts"
            return 1
        fi
        echo "  attempt $attempt/$max_attempts..."
        sleep 6
        ((attempt++))
    done
    echo "Server on port $port is ready."
    return 0
}

kill_vllm() {
    local pids
    pids=$(ps aux | grep "vllm" | grep -v grep | awk '{print $2}')
    if [ -n "$pids" ]; then
        echo "Stopping VLLM processes: $pids"
        for pid in $pids; do kill -2 "$pid" 2>/dev/null || true; done
        sleep 12
        # Force-kill anything that didn't exit cleanly
        pids=$(ps aux | grep "vllm" | grep -v grep | awk '{print $2}')
        for pid in $pids; do kill -9 "$pid" 2>/dev/null || true; done
    fi
}

# ── Per-checkpoint evaluation ────────────────────────────────────

run_evaluation() {
    local lora_name=$1
    local faiss_k=${2:-10}

    activate_conda_env "$ENV_NAME"

    # ── Step 1: HyDE generation via LoRA VLLM ──────────────────
    local lora_path="${ADAPTER_PATH}/${lora_name}"
    echo "Starting HyDE VLLM: model=${MODEL}, lora=${lora_path}"

    python -m vllm.entrypoints.openai.api_server \
        --trust-remote-code \
        --model "${MODEL_PATH}/${MODEL}" \
        --host 0.0.0.0 \
        --port "${VLLM_PORT}" \
        --tensor-parallel-size 1 \
        --max-num-batched-tokens "${MAX_LENGTH}" \
        --served-model-name hyde \
        --gpu-memory-utilization 0.60 \
        --max-model-len "${MAX_LENGTH}" \
        --max-seq-len-to-capture "${MAX_LENGTH}" \
        --swap-space 8 \
        --enable-prefix-caching \
        --enable-lora \
        --lora-modules "hyde-lora=${lora_path}" &

    if ! wait_for_server "${VLLM_PORT}"; then
        echo "HyDE VLLM failed to start; skipping checkpoint ${lora_name}"
        kill_vllm
        return 1
    fi

    bash step1.sh \
        "${lora_name}" \
        "${ANSWER_FILE}" \
        "hyde-lora" \
        "EMPTY" \
        "http://localhost:${VLLM_PORT}/v1" \
        "${OUT_DIR}/${lora_name}"

    kill_vllm

    # ── Step 2: Retrieval metrics ───────────────────────────────
    bash step2.sh \
        "${OUT_DIR}/${lora_name}/result_1.json" \
        "${OUT_DIR}" \
        "${lora_name}" \
        "${faiss_k}" \
        "${ANSWER_FILE}"

    # ── Step 3: Answer quality metrics ─────────────────────────
    local step2_result="${OUT_DIR}/${lora_name}/faiss/result_2.json"

    if [ -z "${JUDGE_MODEL_PATH}" ]; then
        echo "JUDGE_MODEL_PATH is empty; skipping step3 for ${lora_name}"
        return 0
    fi

    if [ ! -f "${step2_result}" ]; then
        echo "step2 result not found (${step2_result}); skipping step3 for ${lora_name}"
        return 0
    fi

    echo "Starting judge VLLM: ${JUDGE_MODEL_PATH}"

    python -m vllm.entrypoints.openai.api_server \
        --trust-remote-code \
        --model "${JUDGE_MODEL_PATH}" \
        --host 0.0.0.0 \
        --port "${JUDGE_PORT}" \
        --tensor-parallel-size 1 \
        --served-model-name judge \
        --gpu-memory-utilization 0.80 &

    if ! wait_for_server "${JUDGE_PORT}"; then
        echo "Judge VLLM failed to start; skipping step3 for ${lora_name}"
        kill_vllm
        return 0
    fi

    bash step3.sh \
        "${step2_result}" \
        "${OUT_DIR}/${lora_name}/faiss" \
        "${JUDGE_MODEL}" \
        "${JUDGE_API_KEY}" \
        "http://localhost:${JUDGE_PORT}/v1"

    kill_vllm
}

# ── Main loop ────────────────────────────────────────────────────

mkdir -p "${OUT_DIR}"

for checkpoint in "${CHECKPOINT_LIST[@]}"; do
    echo ""
    echo "============================================"
    echo "  Checkpoint: ${checkpoint}"
    echo "============================================"
    run_evaluation "${checkpoint}" 10
done

echo ""
echo "All checkpoints evaluated."
