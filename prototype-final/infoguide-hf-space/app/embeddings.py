import json
from pathlib import Path

import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings


MODEL_NAME = "BAAI/bge-m3"

CHUNKS_INPUT_PATH = Path("data/chunks/chunks.json")
INDEXES_DIR = Path("data/indexes")

EMBEDDINGS_OUTPUT_PATH = INDEXES_DIR / "embeddings.npy"
METADATA_OUTPUT_PATH = INDEXES_DIR / "embeddings_metadata.json"


def load_bge_model():
    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    return embeddings


def load_chunks(input_path=CHUNKS_INPUT_PATH):
    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return chunks


def create_embeddings_batch(chunks, embeddings, progress_callback=None, batch_size=32):
    texts = [chunk["text"] for chunk in chunks]
    vectors = []
    total = len(texts)

    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        batch_vectors = embeddings.embed_documents(batch)
        vectors.extend(batch_vectors)
        if progress_callback:
            progress_callback(min(start + batch_size, total), total)

    return np.array(vectors, dtype=np.float32)


def save_embeddings(chunks, vectors):
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    np.save(EMBEDDINGS_OUTPUT_PATH, vectors)

    metadata = []

    for chunk in chunks:
        metadata.append({
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("text"),
            "metadata": {
                **chunk.get("metadata", {}),
                "embedding_model": MODEL_NAME,
                "embedding_dimension": int(vectors.shape[1])
            }
        })

    with open(METADATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return EMBEDDINGS_OUTPUT_PATH, METADATA_OUTPUT_PATH