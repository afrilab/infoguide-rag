import json
from pathlib import Path
from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv

from financerag.generate.openai import OpenAIGenerator

load_dotenv()

RESULTS_CSV = "results/final.csv"
DATASET_DIR = "dataset"
OUTPUT_XLSX = "results/final_with_answers.xlsx"

MODEL_NAME = "gpt-4o-mini"
TOP_K_DOCS = 3
MAX_QUERIES = 1000


def load_jsonl_as_dict(file_path: Path):
    data = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            data[row["_id"]] = row
    return data


def load_all_datasets(dataset_root: Path):
    datasets = {}

    for subset_dir in dataset_root.iterdir():
        if not subset_dir.is_dir():
            continue

        queries_path = subset_dir / "queries.jsonl"
        queries_prep_path = subset_dir / "queries_prep.jsonl"
        corpus_path = subset_dir / "corpus.jsonl"

        if not queries_path.exists():
            continue
        if not queries_prep_path.exists():
            continue
        if not corpus_path.exists():
            continue

        datasets[subset_dir.name] = {
            "queries": load_jsonl_as_dict(queries_path),
            "queries_prep": load_jsonl_as_dict(queries_prep_path),
            "corpus": load_jsonl_as_dict(corpus_path),
        }

        print(f"Loaded dataset: {subset_dir.name}")

    return datasets


def find_subset_for_query_and_doc(query_id, corpus_id, datasets):
    for subset_name, data in datasets.items():
        if query_id in data["queries"] and corpus_id in data["corpus"]:
            return subset_name
    return None


def build_prompt(query_text, expanded_query_text, docs):
    docs_block = []
    for i, doc in enumerate(docs, start=1):
        docs_block.append(f"[Document {i}]\n{doc}")

    joined_docs = "\n\n".join(docs_block)

    system_msg = (
        "You are a financial question answering assistant operating in a retrieval-augmented "
        "generation (RAG) setting.\n\n"
        "You are given:\n"
        "- An original query\n"
        "- An expanded query\n"
        "- A set of retrieved documents\n\n"
        "Your task is to generate a grounded answer using ONLY the provided documents.\n\n"
        "STRICT RULES:\n"
        "1. Use ONLY the information explicitly present in the retrieved documents.\n"
        "2. Do NOT use prior knowledge.\n"
        "3. If the documents do not contain sufficient evidence, respond exactly with:\n"
        "\"Insufficient evidence to answer the question.\"\n"
        "4. If documents contain conflicting information, acknowledge the conflict and explain it.\n"
        "5. Cite document numbers in the answer.\n\n"
        "REASONING GUIDELINES:\n"
        "- Carefully read all documents before answering.\n"
        "- Combine information across multiple documents when needed.\n"
        "- Do NOT assume missing details.\n\n"
        "OUTPUT FORMAT:\n"
        "Answer:\n"
        "<concise and factual answer>\n\n"
        "Evidence:\n"
        "- [Document 1]: <relevant supporting sentence or summary>\n"
        "- [Document 2]: <relevant supporting sentence or summary>\n\n"
        "Notes:\n"
        "- Mention uncertainty or conflicts if present.\n"
        "- If there is no uncertainty or conflict, write: None."
    )

    user_msg = f"""Original query:
{query_text}

Expanded query:
{expanded_query_text}

Retrieved documents:
{joined_docs}

Now answer the original query using only the retrieved documents.
"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def main():
    results_path = Path(RESULTS_CSV)
    dataset_root = Path(DATASET_DIR)
    output_path = Path(OUTPUT_XLSX)

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    df = pd.read_csv(results_path)

    if "query_id" not in df.columns or "corpus_id" not in df.columns:
        raise ValueError(
            f"final.csv must contain query_id and corpus_id. Current columns: {df.columns.tolist()}"
        )

    all_query_ids = df["query_id"].drop_duplicates().tolist()
    print(f"Selected all {len(all_query_ids)} query IDs.")

    datasets = load_all_datasets(dataset_root)

    grouped_docs = defaultdict(list)
    query_info = {}

    for _, row in df.iterrows():
        query_id = row["query_id"]
        corpus_id = row["corpus_id"]

        subset = find_subset_for_query_and_doc(query_id, corpus_id, datasets)
        if subset is None:
            continue

        data = datasets[subset]
        query_text = data["queries"].get(query_id, {}).get("text", "")
        expanded_query_text = data["queries_prep"].get(query_id, {}).get("text", "")
        document_text = data["corpus"].get(corpus_id, {}).get("text", "")

        if query_id not in query_info:
            query_info[query_id] = {
                "subset": subset,
                "query": query_text,
                "expanded_query": expanded_query_text,
            }

        grouped_docs[query_id].append({
            "corpus_id": corpus_id,
            "document": document_text,
        })

    generator = OpenAIGenerator(model_name=MODEL_NAME)

    messages = {}
    for query_id, docs in grouped_docs.items():
        info = query_info[query_id]
        top_docs = [d["document"] for d in docs[:TOP_K_DOCS]]

        messages[query_id] = build_prompt(
            query_text=info["query"],
            expanded_query_text=info["expanded_query"],
            docs=top_docs,
        )

    print(f"Generating answers for {len(messages)} queries...")
    responses = generator.generation(messages=messages, num_processes=1)

    output_rows = []
    for query_id, info in query_info.items():
        docs = grouped_docs[query_id][:TOP_K_DOCS]

        output_rows.append({
            "subset": info["subset"],
            "query_id": query_id,
            "query": info["query"],
            "expanded_query": info["expanded_query"],
            "document_ids": " | ".join([d["corpus_id"] for d in docs]),
            "documents": "\n\n====================\n\n".join([d["document"] for d in docs]),
            "generated_answer": responses.get(query_id, ""),
        })

    out_df = pd.DataFrame(output_rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_excel(output_path, index=False)

    print(f"Done. Saved to: {output_path}")


if __name__ == "__main__":
    main()