import json
import shutil
from pathlib import Path

import bm25s
import Stemmer

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks_v2.jsonl")
SAVE_DIR = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/bm25_index/lotus")

if SAVE_DIR.exists():
    shutil.rmtree(SAVE_DIR)
SAVE_DIR.mkdir(parents=True, exist_ok=True)

docs = []
corpus_texts = []

with INPUT.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        docs.append({
            "id": row["chunk_id"],
            "doc_id": row["doc_id"],
            "source_doc_id": row["source_doc_id"],
            "title": row["title"],
            "text": row["text"],
            "title_summary": row["title_summary"],
            "prev_chunk_id": row["prev_chunk_id"],
            "next_chunk_id": row["next_chunk_id"],
            "bundle_id": row["bundle_id"],
            "date_published": row["date_published"],
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
