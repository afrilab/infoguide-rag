import json
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

INPUT = Path("/cta/users/teoman.arabul/finsage/finance_rag_db/financebench_chunks.jsonl")
PERSIST_DIR = "/cta/users/teoman.arabul/finsage/finance_rag_db/chroma"
COLLECTION_NAME = "lotus"

model = SentenceTransformer("BAAI/bge-m3")

client = chromadb.PersistentClient(path=PERSIST_DIR)
try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.create_collection(name=COLLECTION_NAME)

batch_ids = []
batch_docs = []
batch_embeddings = []
batch_meta = []

BATCH_SIZE = 64
total = 0

with INPUT.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        text = row["text"]
        emb = model.encode(text).tolist()

        batch_ids.append(row["chunk_id"])
        batch_docs.append(text)
        batch_embeddings.append(emb)
        batch_meta.append({
            "doc_id": row["doc_id"],
            "title": row.get("title", "")
        })

        if len(batch_ids) >= BATCH_SIZE:
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_meta
            )
            total += len(batch_ids)
            print(f"Indexed {total} chunks")
            batch_ids, batch_docs, batch_embeddings, batch_meta = [], [], [], []

if batch_ids:
    collection.add(
        ids=batch_ids,
        documents=batch_docs,
        embeddings=batch_embeddings,
        metadatas=batch_meta
    )
    total += len(batch_ids)

print(f"Finished indexing {total} chunks into {PERSIST_DIR}")
