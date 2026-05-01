import json
from pathlib import Path

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/corpus.jsonl")
OUTPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks.jsonl")

CHUNK_SIZE = 1000
OVERLAP = 200

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    text = text or ""
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap

    return chunks

count_docs = 0
count_chunks = 0

with INPUT.open("r", encoding="utf-8") as f, OUTPUT.open("w", encoding="utf-8") as out:
    for line in f:
        row = json.loads(line)

        doc_id = row.get("doc_id") or row.get("id") or row.get("_id")
        title = row.get("title", "")
        text = row.get("text", "") or row.get("contents", "")

        if not doc_id or not text:
            continue

        for i, chunk in enumerate(chunk_text(text)):
            out.write(json.dumps({
                "chunk_id": f"{doc_id}_{i}",
                "doc_id": str(doc_id),
                "title": title,
                "text": chunk
            }, ensure_ascii=False) + "\n")
            count_chunks += 1

        count_docs += 1

print(f"Processed documents: {count_docs}")
print(f"Created chunks: {count_chunks}")
print(f"Saved to: {OUTPUT}")
