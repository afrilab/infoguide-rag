import json
import re
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

    return embeddings, metadata


def build_faiss_index(embeddings):
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
    return re.sub(r"[^\w\s]", "", text.lower()).split()


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


def _rrf_score(ranks, k=60):
    return sum(1.0 / (k + r) for r in ranks)


def retrieve_multi_query(sub_query_vectors, sub_queries, faiss_index, bm25_index, metadata, top_k=5, rrf_k=60, candidate_k=None):
    """Her sub-query için ayrı retrieval yapar, RRF ile birleştirir.
    faiss_index veya bm25_index None geçilirse o retriever atlanır.
    """
    if candidate_k is None:
        candidate_k = max(top_k * 6, 40)

    chunk_data = {}

    for query_vector, query in zip(sub_query_vectors, sub_queries):
        if faiss_index is not None and bm25_index is not None:
            results = retrieve_hybrid(
                query_vector, query, faiss_index, bm25_index, metadata,
                top_k=candidate_k, rrf_k=rrf_k, candidate_k=candidate_k,
            )
        elif faiss_index is not None:
            results = retrieve_with_faiss(query_vector, faiss_index, metadata, top_k=candidate_k)
        else:
            results = retrieve_with_bm25(query, bm25_index, metadata, top_k=candidate_k)

        for rank, result in enumerate(results, start=1):
            doc_id = result.get("metadata", {}).get("document_id", "")
            cid = f"{doc_id}::{result['chunk_id']}"
            contribution = 1.0 / (rrf_k + rank)
            if cid not in chunk_data:
                chunk_data[cid] = {"score": 0.0, "result": result}
            chunk_data[cid]["score"] += contribution

    fused = [{**data["result"], "score": data["score"]} for data in chunk_data.values()]
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused[:top_k]


def retrieve_hybrid(query_vector, query, faiss_index, bm25_index, metadata, top_k=5, rrf_k=60, candidate_k=None):
    """Reciprocal Rank Fusion over FAISS (dense) + BM25 (sparse) results."""
    if candidate_k is None:
        candidate_k = max(top_k * 4, 20)

    faiss_results = retrieve_with_faiss(query_vector, faiss_index, metadata, top_k=candidate_k)
    bm25_results = retrieve_with_bm25(query, bm25_index, metadata, top_k=candidate_k)

    chunk_ranks = {}

    for rank, result in enumerate(faiss_results, start=1):
        doc_id = result.get("metadata", {}).get("document_id", "")
        cid = f"{doc_id}::{result['chunk_id']}"
        chunk_ranks.setdefault(cid, {"faiss_rank": None, "bm25_rank": None, "result": result})
        chunk_ranks[cid]["faiss_rank"] = rank

    for rank, result in enumerate(bm25_results, start=1):
        doc_id = result.get("metadata", {}).get("document_id", "")
        cid = f"{doc_id}::{result['chunk_id']}"
        if cid not in chunk_ranks:
            chunk_ranks[cid] = {"faiss_rank": None, "bm25_rank": None, "result": result}
        chunk_ranks[cid]["bm25_rank"] = rank

    fused = []
    for cid, data in chunk_ranks.items():
        ranks = [r for r in [data["faiss_rank"], data["bm25_rank"]] if r is not None]
        rrf = _rrf_score(ranks, k=rrf_k)
        entry = {
            **data["result"],
            "score": rrf,
            "faiss_rank": data["faiss_rank"],
            "bm25_rank": data["bm25_rank"],
        }
        fused.append(entry)

    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused[:top_k]