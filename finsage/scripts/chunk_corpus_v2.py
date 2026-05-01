import json
from pathlib import Path

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/corpus.jsonl")
OUTPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks_v2.jsonl")

CHUNK_SIZE = 1000
OVERLAP = 200
TS_SUMMARY_CHARS = 300

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

        source_doc_id = row.get("doc_id") or row.get("id") or row.get("_id")
        title = row.get("title", "") or ""
        text = row.get("text", "") or row.get("contents", "")

        if not source_doc_id or not text:
            continue

        pieces = chunk_text(text)

        for i, chunk in enumerate(pieces):
            chunk_id = f"{source_doc_id}_{i}"
            prev_chunk_id = f"{source_doc_id}_{i-1}" if i > 0 else ""
            next_chunk_id = f"{source_doc_id}_{i+1}" if i < len(pieces) - 1 else ""
            summary = chunk[:TS_SUMMARY_CHARS].strip()
            title_summary = f"{title}\n{summary}".strip()

            out.write(json.dumps({
                "chunk_id": chunk_id,
                "doc_id": chunk_id,                  # important: matches Chroma id
                "source_doc_id": str(source_doc_id), # original FinanceRAG doc id
                "title": title,
                "text": chunk,
                "prev_chunk_id": prev_chunk_id,
                "next_chunk_id": next_chunk_id,
                "bundle_id": None,
                "title_summary": title_summary,
                "date_published": row.get("date_published") or row.get("date") or row.get("filing_date") or "2023-01-01",
            }, ensure_ascii=False) + "\n")
            count_chunks += 1

        count_docs += 1

print(f"Processed documents: {count_docs}")
print(f"Created chunks: {count_chunks}")
print(f"Saved to: {OUTPUT}")
