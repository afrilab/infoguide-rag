import json
from pathlib import Path

import bm25s
import Stemmer

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks.jsonl")
SAVE_DIR = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/bm25_index/lotus")

SAVE_DIR.mkdir(parents=True, exist_ok=True)

docs = []
corpus_texts = []

with INPUT.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        docs.append({
            "id": row["chunk_id"],
            "doc_id": row["doc_id"],
            "title": row.get("title", ""),
            "text": row["text"],
        })
        corpus_texts.append(row["text"])

print(f"[INFO] Loaded {len(corpus_texts)} chunk-docs")

stemmer = Stemmer.Stemmer("english")
corpus_tokens = bm25s.tokenize(
    corpus_texts,
    stopwords="en",
    stemmer=stemmer,
)

print("[INFO] Tokenization done")

retriever = bm25s.BM25()
retriever.index(corpus_tokens)

print("[INFO] BM25 indexing done")

retriever.save(str(SAVE_DIR), corpus=docs)

print(f"[INFO] BM25 index saved to {SAVE_DIR}")
print("[INFO] Done")
