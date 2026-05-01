import json
import shutil
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks_v2.jsonl")
ROOT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db")
CHROMA_DIR = ROOT / "chroma"
TS_CHROMA_DIR = ROOT / "ts_chroma"
COLLECTION = "lotus"

# clean rebuild
if CHROMA_DIR.exists():
    shutil.rmtree(CHROMA_DIR)
if TS_CHROMA_DIR.exists():
    shutil.rmtree(TS_CHROMA_DIR)

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

main_store = Chroma(
    collection_name=COLLECTION,
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIR),
)

ts_store = Chroma(
    collection_name=COLLECTION,
    embedding_function=embeddings,
    persist_directory=str(TS_CHROMA_DIR),
)

ids = []
texts = []
metadatas = []

ts_ids = []
ts_texts = []
ts_metas = []

with INPUT.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)

        ids.append(row["chunk_id"])
        texts.append(row["text"])
        metadatas.append({
            "doc_id": row["doc_id"],
            "source_doc_id": row["source_doc_id"],
            "title": row["title"],
            "prev_chunk_id": row["prev_chunk_id"],
            "next_chunk_id": row["next_chunk_id"],
            "bundle_id": row["bundle_id"],
            "title_summary": row["title_summary"],
            "date_published": row["date_published"],
        })

        ts_ids.append(row["chunk_id"])
        ts_texts.append(row["title_summary"])
        ts_metas.append({
            "doc_id": row["doc_id"],
            "source_doc_id": row["source_doc_id"],
            "title": row["title"],
            "date_published": row["date_published"],
        })

BATCH = 64

for i in range(0, len(ids), BATCH):
    main_store.add_texts(
        texts=texts[i:i+BATCH],
        metadatas=metadatas[i:i+BATCH],
        ids=ids[i:i+BATCH],
    )
    print(f"[INFO] Main Chroma indexed {min(i+BATCH, len(ids))}/{len(ids)}")

for i in range(0, len(ts_ids), BATCH):
    ts_store.add_texts(
        texts=ts_texts[i:i+BATCH],
        metadatas=ts_metas[i:i+BATCH],
        ids=ts_ids[i:i+BATCH],
    )
    print(f"[INFO] TS Chroma indexed {min(i+BATCH, len(ts_ids))}/{len(ts_ids)}")

print("[INFO] Finished rebuilding chroma and ts_chroma")
