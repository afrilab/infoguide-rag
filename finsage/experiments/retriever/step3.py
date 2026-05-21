"""
Step 3: Answer Generation + LLM-Judge Quality Evaluation
=========================================================

For each question in step2 output:
  1. Generates an answer from the retrieved context via LLM (RAG generation).
  2. Evaluates the answer with an LLM judge across five dimensions:
       - faithfulness       (1-5)   : every claim grounded in context
       - evidence_grounding (0-1)   : fraction of facts traceable to a chunk
       - answer_relevance   (1-5)   : answer directly addresses the question
       - hallucination_rate (0-1)   : fraction of answer that is fabricated
       - verdict            PASS / PARTIAL / FAIL

Input  (result_2.json from step2)
-------
[
    { -- summary row (index 0) -- "avg_recall": ..., ... },
    {
        "question": "...",
        "retrieved_context": ["chunk text 1", "chunk text 2", ...],
        "recall": 0.8,
        ...
    },
    ...
]

Output (result_3.json)
--------
[
    { -- extended summary --
        ...all step2 summary fields...,
        "avg_faithfulness":       4.1,
        "avg_evidence_grounding": 0.83,
        "avg_answer_relevance":   4.3,
        "avg_hallucination_rate": 0.07,
        "pass_rate":   0.72,
        "partial_rate": 0.20,
        "fail_rate":   0.08,
        "error_count": 0
    },
    {
        ...all step2 per-question fields...,
        "generated_answer":   "...",
        "faithfulness":       4,
        "evidence_grounding": 0.85,
        "answer_relevance":   5,
        "hallucination_rate": 0.05,
        "verdict":            "PASS",
        "judge_reasoning":    "All claims are directly supported by the provided context."
    },
    ...
]
"""

import os
import sys
import re
import json
import logging
import argparse
from tqdm import tqdm
from openai import OpenAI

logging.basicConfig(
    filemode="w",
    filename="step3.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Max characters fed to the LLM to stay within context budgets
MAX_CONTEXT_CHARS = 6000   # ~1 500 tokens  — for answer generation
MAX_JUDGE_CHARS   = 4000   # ~1 000 tokens  — for the judge (smaller to leave room for response)

# ── Prompts ───────────────────────────────────────────────────────────────────

ANSWER_SYS_PROMPT = (
    "You are a financial analyst assistant. "
    "Answer the question using ONLY the information present in the retrieved context below. "
    "Be concise, accurate, and factual. "
    "If the context does not contain enough information to answer, state that explicitly."
)

JUDGE_SYS_PROMPT = """\
You are an expert evaluator of RAG (Retrieval-Augmented Generation) systems for financial documents.
Given a question, the retrieved context, and a generated answer, score the answer on five dimensions.
Return ONLY a valid JSON object — no markdown fences, no extra text.

JSON schema:
{
  "faithfulness":       <integer 1-5>,
  "evidence_grounding": <float   0.0-1.0>,
  "answer_relevance":   <integer 1-5>,
  "hallucination_rate": <float   0.0-1.0>,
  "verdict":            "<PASS|PARTIAL|FAIL>",
  "reasoning":          "<one concise sentence>"
}

Scoring guide
─────────────
faithfulness (1-5)
  Does every factual claim in the answer appear in the context?
  1 = most claims have no support  |  5 = every claim is grounded in the context

evidence_grounding (0.0-1.0)
  What fraction of the answer's specific facts can be traced to a numbered context chunk?
  0.0 = nothing is traceable  |  1.0 = every fact is traceable to a chunk

answer_relevance (1-5)
  Does the answer directly address what the question is asking?
  1 = completely off-topic  |  5 = fully and directly answers the question

hallucination_rate (0.0-1.0)
  What fraction of the answer contains information fabricated beyond the context?
  0.0 = no hallucination  |  1.0 = entirely fabricated

verdict
  PASS    — faithfulness >= 4  AND  answer_relevance >= 4  AND  hallucination_rate <= 0.15
  FAIL    — faithfulness <= 2  OR   answer_relevance <= 2  OR   hallucination_rate >= 0.50
  PARTIAL — all other cases\
"""


# ── Utilities ─────────────────────────────────────────────────────────────────

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def format_context(chunks: list[str], max_chars: int) -> str:
    """Number each chunk and truncate so the total stays within max_chars."""
    parts = []
    total = 0
    for i, chunk in enumerate(chunks, 1):
        line = f"[{i}] {chunk.strip()}"
        if total + len(line) > max_chars:
            break
        parts.append(line)
        total += len(line) + 2  # +2 for "\n\n"
    return "\n\n".join(parts)


def extract_json(text: str) -> dict:
    """Parse a JSON object from LLM output, tolerating markdown code fences."""
    text = text.strip()
    # Try to strip ```json ... ``` fences first
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    # Then try raw {...}
    raw = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if raw:
        return json.loads(raw.group(0))
    raise ValueError(f"No JSON object found in output: {text[:300]!r}")


def _clamp_int(v, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return -1


def _clamp_float(v, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return -1.0


def validate_metrics(raw: dict) -> dict:
    """Clamp all metric values to their declared ranges."""
    verdict = raw.get("verdict", "ERROR")
    if verdict not in ("PASS", "PARTIAL", "FAIL"):
        verdict = "ERROR"
    return {
        "faithfulness":       _clamp_int(raw.get("faithfulness"),       1, 5),
        "evidence_grounding": _clamp_float(raw.get("evidence_grounding"), 0.0, 1.0),
        "answer_relevance":   _clamp_int(raw.get("answer_relevance"),   1, 5),
        "hallucination_rate": _clamp_float(raw.get("hallucination_rate"), 0.0, 1.0),
        "verdict":            verdict,
        "reasoning":          str(raw.get("reasoning", ""))[:500],
    }


# ── LLM calls ─────────────────────────────────────────────────────────────────

def generate_answer(question: str, context: str, model: str, client: OpenAI) -> str:
    if not context.strip():
        return "No relevant context was retrieved for this question."
    user_msg = f"Context:\n{context[:MAX_CONTEXT_CHARS]}\n\nQuestion: {question}\n\nAnswer:"
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": ANSWER_SYS_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.0,
                max_tokens=512,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logging.warning(f"Answer generation attempt {attempt + 1}/3 failed: {exc}")
    return "ERROR: answer generation failed after 3 attempts."


def evaluate_answer(question: str, context: str, answer: str, model: str, client: OpenAI) -> dict:
    user_msg = (
        f"Question:\n{question}\n\n"
        f"Retrieved Context:\n{context[:MAX_JUDGE_CHARS]}\n\n"
        f"Generated Answer:\n{answer}\n\n"
        "Return the evaluation JSON:"
    )
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": JUDGE_SYS_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.0,
                max_tokens=256,
            )
            raw = extract_json(resp.choices[0].message.content)
            return validate_metrics(raw)
        except Exception as exc:
            logging.warning(f"Judge evaluation attempt {attempt + 1}/3 failed: {exc}")
    return {
        "faithfulness":       -1,
        "evidence_grounding": -1.0,
        "answer_relevance":   -1,
        "hallucination_rate": -1.0,
        "verdict":            "ERROR",
        "reasoning":          "Evaluation failed after 3 attempts.",
    }


# ── Core logic ────────────────────────────────────────────────────────────────

def run_step3(input_file: str, output_dir: str, model: str, api_key: str, base_url: str):
    data = load_json(input_file)
    if not data:
        logging.error("Input file is empty")
        return

    # step2 places a summary dict at index 0; per-question results start at index 1
    step2_summary  = data[0]
    per_question   = data[1:]

    if not per_question:
        logging.error("No per-question entries found in input file")
        return

    # Warn if retrieved_context is missing (i.e., old step2 output without the field)
    missing_ctx = sum(1 for e in per_question if not e.get("retrieved_context"))
    if missing_ctx:
        logging.warning(
            f"{missing_ctx}/{len(per_question)} entries are missing 'retrieved_context'. "
            "Re-run step2 with the updated step2.py to populate this field."
        )

    client  = OpenAI(api_key=api_key, base_url=base_url)
    results = []

    for idx, entry in tqdm(enumerate(per_question), total=len(per_question), desc="step3"):
        question        = entry.get("question", "")
        retrieved_chunks = entry.get("retrieved_context", [])
        context          = format_context(retrieved_chunks, MAX_CONTEXT_CHARS)

        answer  = generate_answer(question, context, model, client)
        logging.info(f"[{idx}] answer[:120]: {answer[:120]}")

        metrics = evaluate_answer(question, context, answer, model, client)
        logging.info(f"[{idx}] metrics: {metrics}")

        results.append({
            **entry,
            "generated_answer":   answer,
            "faithfulness":       metrics["faithfulness"],
            "evidence_grounding": metrics["evidence_grounding"],
            "answer_relevance":   metrics["answer_relevance"],
            "hallucination_rate": metrics["hallucination_rate"],
            "verdict":            metrics["verdict"],
            "judge_reasoning":    metrics["reasoning"],
        })

    # ── Aggregate ────────────────────────────────────────────────
    valid   = [r for r in results if r["verdict"] != "ERROR"]
    n_valid = len(valid) or 1

    def _avg(key):
        vals = [r[key] for r in valid if isinstance(r[key], (int, float)) and r[key] >= 0]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    verdicts = [r["verdict"] for r in valid]
    summary  = {
        **step2_summary,
        "avg_faithfulness":       _avg("faithfulness"),
        "avg_evidence_grounding": _avg("evidence_grounding"),
        "avg_answer_relevance":   _avg("answer_relevance"),
        "avg_hallucination_rate": _avg("hallucination_rate"),
        "pass_rate":    round(verdicts.count("PASS")    / n_valid, 4),
        "partial_rate": round(verdicts.count("PARTIAL") / n_valid, 4),
        "fail_rate":    round(verdicts.count("FAIL")    / n_valid, 4),
        "error_count":  len(results) - len(valid),
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "result_3.json")
    save_json([summary] + results, out_path)
    logging.info(f"Results saved to {out_path}")

    # ── Console summary ──────────────────────────────────────────
    print("\n=== Step 3 — Answer Quality Summary ===")
    print(f"  Questions evaluated : {len(valid)} / {len(results)}")
    print(f"  Faithfulness        : {summary['avg_faithfulness']:.3f} / 5")
    print(f"  Evidence Grounding  : {summary['avg_evidence_grounding']:.3f}")
    print(f"  Answer Relevance    : {summary['avg_answer_relevance']:.3f} / 5")
    print(f"  Hallucination Rate  : {summary['avg_hallucination_rate']:.3f}")
    print(f"  Verdicts  PASS      : {summary['pass_rate']*100:.1f}%")
    print(f"            PARTIAL   : {summary['partial_rate']*100:.1f}%")
    print(f"            FAIL      : {summary['fail_rate']*100:.1f}%")
    if summary["error_count"]:
        print(f"  Errors              : {summary['error_count']}  (see step3.log)")
    print(f"  Output              : {out_path}")

    # ── Retrieval summary from step2 (for easy cross-reference) ─
    if "avg_recall" in step2_summary:
        print("\n=== Step 2 — Retrieval Summary (for reference) ===")
        print(f"  Recall    : {step2_summary.get('avg_recall', 0):.4f}")
        print(f"  Precision : {step2_summary.get('avg_precision', 0):.4f}")
        print(f"  F1        : {step2_summary.get('avg_f1', 0):.4f}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 3: RAG answer generation + LLM-judge quality evaluation"
    )
    parser.add_argument("--input",      required=True,
                        help="Path to result_2.json produced by step2")
    parser.add_argument("--output",     required=True,
                        help="Output directory (result_3.json will be written here)")
    parser.add_argument("--model_name", default="judge",
                        help="Judge / answer-gen LLM served-model name")
    parser.add_argument("--api_key",    default="EMPTY",
                        help="LLM API key (use 'EMPTY' for local VLLM)")
    parser.add_argument("--base_url",   default="http://localhost:8001/v1",
                        help="LLM API base URL")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logging.error(f"Input file not found: {args.input}")
        sys.exit(1)

    run_step3(args.input, args.output, args.model_name, args.api_key, args.base_url)


if __name__ == "__main__":
    main()
