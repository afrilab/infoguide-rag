import json
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi


INDEXES_DIR = Path("data/indexes")

EMBEDDINGS_PATH = INDEXES_DIR / "embeddings.npy"
METADATA_PATH = INDEXES_DIR / "embeddings_metadata.json"


def load_embeddings_and_metadata():
    embeddings = np.load(EMBEDDINGS_PATH)

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    embeddings = embeddings.astype("float32")

    return embeddings, metadata


def build_faiss_index(embeddings):
    embeddings = embeddings.astype("float32")

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def retrieve_with_faiss(query_vector, faiss_index, metadata, top_k=5):
    scores, indices = faiss_index.search(query_vector, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        chunk = metadata[idx]

        results.append({
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("text"),
            "score": float(score),
            "metadata": chunk.get("metadata", {})
        })

    return results


def simple_tokenize(text):
    return text.lower().split()


def build_bm25_index(metadata):
    corpus = [item["text"] for item in metadata]
    tokenized_corpus = [simple_tokenize(text) for text in corpus]

    bm25 = BM25Okapi(tokenized_corpus)

    return bm25


def retrieve_with_bm25(query, bm25_index, metadata, top_k=5):
    tokenized_query = simple_tokenize(query)

    scores = bm25_index.get_scores(tokenized_query)

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for idx in top_indices:
        chunk = metadata[idx]

        results.append({
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("text"),
            "score": float(scores[idx]),
            "metadata": chunk.get("metadata", {})
        })

    return results