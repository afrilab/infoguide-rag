import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import json
import re
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion import extract_text, sanitize_document_stem
from preprocessing import preprocess_text
from chunking import chunk_text, save_chunks
from embeddings import load_bge_model, create_embeddings_batch, save_embeddings, MODEL_NAME
from image_description import run_image_description, load_vision_client
from query_processing import (
    load_gpt_client,
    expand_query_with_gpt,
    decompose_query_with_gpt,
    create_sub_query_embeddings,
)
from retrieval import (
    load_embeddings_and_metadata,
    build_faiss_index,
    build_bm25_index,
    retrieve_multi_query,
)
from reranking import load_reranker_model, rerank_results
from generation import generate_answer_with_gpt


CHUNKS_PATH = Path("data/chunks/chunks.json")
INDEXES_DIR = Path("data/indexes")
EMBEDDINGS_PATH = INDEXES_DIR / "embeddings.npy"
METADATA_PATH = INDEXES_DIR / "embeddings_metadata.json"


def _save_chat_chunks(new_chunks, document_id):
    """Merges chunks into chunks.json instead of overwriting it, replacing any
    prior entries that belong to the same document_id (re-uploads)."""
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    kept = [c for c in existing if c.get("metadata", {}).get("document_id") != document_id]
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(kept + new_chunks, f, ensure_ascii=False, indent=4)


def _accumulate_chat_embeddings(new_chunks, new_vectors, document_id):
    """Appends chunk embeddings to the global index instead of overwriting it
    (save_embeddings replaces the whole file), replacing any prior entries for
    the same document_id so documents stay queryable across chat sessions."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    existing_vectors, existing_metadata = None, []
    if EMBEDDINGS_PATH.exists() and METADATA_PATH.exists():
        existing_vectors = np.load(EMBEDDINGS_PATH)
        with open(METADATA_PATH, encoding="utf-8") as f:
            existing_metadata = json.load(f)

    keep_mask = np.array(
        [m.get("metadata", {}).get("document_id") != document_id for m in existing_metadata],
        dtype=bool,
    )
    kept_metadata = [m for m, keep in zip(existing_metadata, keep_mask) if keep]
    kept_vectors = existing_vectors[keep_mask] if existing_vectors is not None and len(keep_mask) else existing_vectors

    new_metadata = [
        {
            "chunk_id": c.get("chunk_id"),
            "text": c.get("text"),
            "metadata": {
                **c.get("metadata", {}),
                "embedding_model": MODEL_NAME,
                "embedding_dimension": int(new_vectors.shape[1]),
            },
        }
        for c in new_chunks
    ]

    all_metadata = kept_metadata + new_metadata
    all_vectors = (
        np.vstack([kept_vectors, new_vectors])
        if kept_vectors is not None and len(kept_vectors)
        else new_vectors
    )

    np.save(EMBEDDINGS_PATH, all_vectors)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)


def _stamp_image_chunk_document_ids(image_paths, document_id):
    """run_image_description persists image chunks internally before we get a
    chance to tag them — patch document_id onto the just-saved entries here,
    matched by their unique image_path."""
    image_path_set = set(image_paths)
    if not image_path_set:
        return

    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH, encoding="utf-8") as f:
            all_chunks = json.load(f)
        for c in all_chunks:
            if c.get("metadata", {}).get("image_path") in image_path_set:
                c["metadata"]["document_id"] = document_id
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=4)

    if METADATA_PATH.exists():
        with open(METADATA_PATH, encoding="utf-8") as f:
            all_metadata = json.load(f)
        for m in all_metadata:
            if m.get("metadata", {}).get("image_path") in image_path_set:
                m["metadata"]["document_id"] = document_id
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)


class _State:
    _bge_model = None
    _reranker = None
    _gpt_client = None
    _vision_client = None
    _index_cache = None

    def get_query_indexes(self, document_ids):
        """Returns (vectors, metadata, faiss_index, bm25_index) for the given
        document scope, rebuilding only when the embeddings file has changed
        or the requested document scope differs from the cached one — instead
        of rebuilding FAISS/BM25 from scratch on every chat message."""
        mtime = EMBEDDINGS_PATH.stat().st_mtime if EMBEDDINGS_PATH.exists() else None
        cache_key = (mtime, tuple(sorted(document_ids)))

        if self._index_cache is not None and self._index_cache[0] == cache_key:
            return self._index_cache[1]

        vectors, metadata = load_embeddings_and_metadata()

        if document_ids:
            doc_id_set = set(document_ids)
            keep_mask = np.array(
                [m.get("metadata", {}).get("document_id") in doc_id_set for m in metadata],
                dtype=bool,
            )
            # Only scope down when we actually find matches — older chunks predating
            # document_id tagging won't match anything, so fall back to the full index.
            if keep_mask.any():
                vectors = vectors[keep_mask]
                metadata = [m for m, keep in zip(metadata, keep_mask) if keep]

        faiss_index = build_faiss_index(vectors)
        bm25_index = build_bm25_index(metadata)

        result = (vectors, metadata, faiss_index, bm25_index)
        self._index_cache = (cache_key, result)
        return result

    def bge(self):
        if self._bge_model is None:
            print("Loading BGE-M3...")
            self._bge_model = load_bge_model()
            print("BGE-M3 ready.")
        return self._bge_model

    def reranker_model(self):
        if self._reranker is None:
            print("Loading reranker...")
            self._reranker = load_reranker_model()
            print("Reranker ready.")
        return self._reranker

    def gpt(self):
        if self._gpt_client is None:
            self._gpt_client = load_gpt_client()
        return self._gpt_client

    def vision(self):
        if self._vision_client is None:
            self._vision_client = load_vision_client()
        return self._vision_client


state = _State()
chat_documents: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting (models will load on first request).")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_expand_output(raw_output: str, original_query: str) -> dict:
    intent = ""
    keywords: list = []
    expanded_query = original_query

    for line in raw_output.splitlines():
        line = line.strip()
        low = line.lower()
        if low.startswith("intent:"):
            intent = line.split(":", 1)[1].strip()
        elif low.startswith("keywords:"):
            kw_raw = line.split(":", 1)[1].strip()
            keywords = [k.strip() for k in kw_raw.split(",") if k.strip()]
        elif low.startswith("expanded query:"):
            expanded_query = line.split(":", 1)[1].strip()

    return {"intent": intent, "keywords": keywords, "expandedQuery": expanded_query}


# ─── Ingestion ────────────────────────────────────────────────────────────────

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = extract_text(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    (Path("data/processed") / "raw_text.txt").write_text(raw_text, encoding="utf-8")

    page_count = raw_text.count("--- Page ")
    image_count = raw_text.count("[Image extracted:")
    table_count = raw_text.count(" Table ")

    return {
        "fileName": file.filename,
        "pages": max(page_count, 1),
        "extractedImages": image_count,
        "extractedTables": table_count,
        "rawText": raw_text,
    }


# ─── Preprocessing ────────────────────────────────────────────────────────────

class PreprocessRequest(BaseModel):
    raw_text: str


@app.post("/preprocess")
async def preprocess(req: PreprocessRequest):
    cleaned_text, _logs = preprocess_text(req.raw_text)

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    (Path("data/processed") / "cleaned_text.txt").write_text(cleaned_text, encoding="utf-8")

    orig = req.raw_text
    stats = {
        "removedInvisibleChars": sum(1 for c in orig if ord(c) < 32 and c not in "\n\t\r"),
        "fixedHyphenations": orig.count("-\n"),
        "removedHeaders": orig.count("--- Page "),
        "removedFooters": 0,
        "normalizedSpaces": max(0, orig.count("  ") - cleaned_text.count("  ")),
    }

    return {"stats": stats, "cleanedText": cleaned_text}


# ─── Chunking ─────────────────────────────────────────────────────────────────

class ChunkRequest(BaseModel):
    cleaned_text: str


@app.post("/chunk")
async def chunk(req: ChunkRequest):
    chunks, _logs = chunk_text(req.cleaned_text)
    save_chunks(chunks)

    frontend_chunks = [
        {
            "id": str(c["chunk_id"]),
            "heading": c.get("heading", ""),
            "text": c.get("text", ""),
            "metadata": {
                "sectionIndex": c.get("metadata", {}).get("section_index", 0),
                "charCount": c.get("char_count", 0),
                "pageNumbers": [
                    p
                    for p in [
                        c.get("metadata", {}).get("start_page"),
                        c.get("metadata", {}).get("end_page"),
                    ]
                    if p
                ],
            },
        }
        for c in chunks
    ]

    return {"totalChunks": len(chunks), "chunks": frontend_chunks}


# ─── Embedding ────────────────────────────────────────────────────────────────

class EmbedRequest(BaseModel):
    chunks: List[Any]


@app.post("/embed")
async def embed(req: EmbedRequest):
    chunks_path = Path("data/chunks/chunks.json")
    if not chunks_path.exists():
        raise HTTPException(status_code=400, detail="No chunks found. Run chunking first.")

    with open(chunks_path, encoding="utf-8") as f:
        chunks = json.load(f)

    t0 = time.time()
    vectors = create_embeddings_batch(chunks, state.bge())
    elapsed = round(time.time() - t0, 1)

    save_embeddings(chunks, vectors)

    return {
        "model": "BAAI/bge-m3",
        "dimension": int(vectors.shape[1]),
        "totalChunks": len(chunks),
        "processingTimeSeconds": elapsed,
        "normalizedVectors": True,
    }


# ─── Image Description ────────────────────────────────────────────────────────

class DescribeImagesRequest(BaseModel):
    chunks: List[Any]


@app.post("/describe-images")
async def describe_images(req: DescribeImagesRequest):
    image_chunks, logs = run_image_description(
        client=state.vision(),
        bge_model=state.bge(),
    )

    skipped = sum(1 for l in logs if "already" in l.lower() or "skipping" in l.lower())

    frontend_image_chunks = [
        {
            "id": str(c["chunk_id"]),
            "imageFile": c.get("metadata", {}).get("image_path", ""),
            "heading": c.get("heading", ""),
            "text": c.get("text", ""),
            "metadata": {
                "type": "image_description",
                "pageNumber": c.get("metadata", {}).get("page_number"),
                "dimensions": "",
            },
        }
        for c in image_chunks
    ]

    return {
        "processed": len(image_chunks),
        "skipped": skipped,
        "newTotalChunks": len(req.chunks) + len(image_chunks),
        "imageChunks": frontend_image_chunks,
    }


# ─── Query Expansion ──────────────────────────────────────────────────────────

class QueryExpansionRequest(BaseModel):
    query: str


@app.post("/expand-query")
async def expand_query(req: QueryExpansionRequest):
    raw_output, _expanded = expand_query_with_gpt(req.query, state.gpt())
    return _parse_expand_output(raw_output, req.query)


# ─── Query Decomposition ─────────────────────────────────────────────────────

class QueryDecompositionRequest(BaseModel):
    query: str


@app.post("/decompose-query")
async def decompose_query(req: QueryDecompositionRequest):
    sub_queries = decompose_query_with_gpt(req.query, state.gpt())
    return {"subQueries": sub_queries}


# ─── Retrieval ────────────────────────────────────────────────────────────────

class RetrievalRequest(BaseModel):
    query: str
    expanded_query: Optional[str] = None
    method: str = "hybrid"
    top_k: int = 5


@app.post("/retrieve")
async def retrieve(req: RetrievalRequest):
    try:
        vectors, metadata = load_embeddings_and_metadata()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Embeddings not found. Run embedding first. ({e})",
        )

    faiss_index = build_faiss_index(vectors)
    bm25_index = build_bm25_index(metadata)

    sub_queries = decompose_query_with_gpt(req.query, state.gpt())
    sub_vectors = create_sub_query_embeddings(sub_queries, state.bge())

    results = retrieve_multi_query(
        sub_vectors, sub_queries, faiss_index, bm25_index, metadata, top_k=req.top_k
    )

    frontend_results = [
        {
            "rank": i + 1,
            "chunkId": str(r.get("chunk_id", "")),
            "heading": r.get("metadata", {}).get("heading", ""),
            "text": r.get("text", ""),
            "score": round(float(r.get("score", 0.0)), 4),
            "faissRank": r.get("faiss_rank") or 0,
            "bm25Rank": r.get("bm25_rank") or 0,
        }
        for i, r in enumerate(results)
    ]

    return {"method": req.method, "topK": req.top_k, "results": frontend_results}


# ─── Reranking ────────────────────────────────────────────────────────────────

class RerankRequest(BaseModel):
    query: str
    chunks: List[Any]
    top_k: int = 5


@app.post("/rerank")
async def rerank(req: RerankRequest):
    internal_chunks = [
        {
            "chunk_id": c.get("chunkId") or c.get("chunk_id", ""),
            "text": c.get("text", ""),
            "heading": c.get("heading", ""),
            "metadata": {"heading": c.get("heading", ""), **(c.get("metadata") or {})},
            "score": float(c.get("score", 0.0)),
        }
        for c in req.chunks
    ]

    reranked = rerank_results(req.query, internal_chunks, state.reranker_model(), top_k=req.top_k)

    chunk_id_to_original_rank = {
        str(c.get("chunkId") or c.get("chunk_id", "")): i + 1
        for i, c in enumerate(req.chunks)
    }

    frontend_results = [
        {
            "newRank": i + 1,
            "originalRank": chunk_id_to_original_rank.get(str(r.get("chunk_id", "")), i + 1),
            "chunkId": str(r.get("chunk_id", "")),
            "heading": r.get("metadata", {}).get("heading", r.get("heading", "")),
            "text": r.get("text", ""),
            "rerankScore": round(float(r.get("rerank_score", 0.0)), 4),
            "originalScore": round(float(r.get("score", 0.0)), 4),
        }
        for i, r in enumerate(reranked)
    ]

    return {"topK": req.top_k, "results": frontend_results}


# ─── Generation ───────────────────────────────────────────────────────────────

class GenerationRequest(BaseModel):
    query: str
    chunks: List[Any]


@app.post("/generate")
async def generate(req: GenerationRequest):
    internal_chunks = [
        {
            "chunk_id": c.get("chunkId") or c.get("chunk_id", ""),
            "text": c.get("text", ""),
            "heading": c.get("heading", ""),
            "metadata": {
                "chunk_type": "chunk",
                "heading": c.get("heading", ""),
                **(c.get("metadata") or {}),
            },
        }
        for c in req.chunks
    ]

    answer = generate_answer_with_gpt(req.query, internal_chunks, state.gpt())

    cited = [
        {"chunkId": str(c["chunk_id"]), "heading": c["heading"]}
        for c in internal_chunks
    ]

    return {
        "model": "gpt-4o-mini",
        "answer": answer,
        "citedChunks": cited,
        "inputTokens": 0,
        "outputTokens": 0,
    }


# ─── Chat: Process Document ───────────────────────────────────────────────────

@app.post("/chat/process")
async def chat_process(file: UploadFile = File(...)):
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = extract_text(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    document_id = str(uuid.uuid4())
    document_stem = sanitize_document_stem(Path(file_path).stem)

    cleaned_text, _ = preprocess_text(raw_text)
    chunks, _ = chunk_text(cleaned_text)
    for c in chunks:
        c.setdefault("metadata", {})["document_id"] = document_id
    _save_chat_chunks(chunks, document_id)

    vectors = create_embeddings_batch(chunks, state.bge())
    _accumulate_chat_embeddings(chunks, vectors, document_id)

    image_chunks, _ = run_image_description(
        client=state.vision(),
        bge_model=state.bge(),
    )
    new_image_paths = [
        c["metadata"]["image_path"]
        for c in image_chunks
        if c.get("metadata", {}).get("source_document") == document_stem
    ]
    _stamp_image_chunk_document_ids(new_image_paths, document_id)

    page_count = len(re.findall(r"--- Page \d+ ---", raw_text))
    total_chunks = len(chunks) + len(image_chunks)

    chat_documents[document_id] = {"file_path": str(file_path)}

    return {
        "pageCount": max(page_count, 1),
        "chunkCount": total_chunks,
        "documentId": document_id,
    }


# ─── Chat: Query ──────────────────────────────────────────────────────────────

class ChatQueryRequest(BaseModel):
    query: str
    document_ids: List[str]


@app.post("/chat/query")
async def chat_query(req: ChatQueryRequest):
    try:
        _vectors, metadata, faiss_index, bm25_index = state.get_query_indexes(req.document_ids)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No embeddings found. Process a document first. ({e})",
        )

    _raw_expansion, expanded_query = expand_query_with_gpt(req.query, state.gpt())
    sub_queries = decompose_query_with_gpt(expanded_query, state.gpt())
    sub_vectors = create_sub_query_embeddings(sub_queries, state.bge())

    # Broader queries decompose into more sub-queries; scale retrieval depth
    # with that signal instead of using a one-size-fits-all top_k.
    dynamic_top_k = min(20, max(5, len(sub_queries) * 4))

    retrieved = retrieve_multi_query(
        sub_vectors, sub_queries, faiss_index, bm25_index, metadata, top_k=dynamic_top_k
    )
    reranked = rerank_results(req.query, retrieved, state.reranker_model(), top_k=dynamic_top_k)
    answer = generate_answer_with_gpt(req.query, reranked, state.gpt())

    sources = [
        {
            "chunkId": str(r.get("chunk_id", "")),
            "heading": r.get("metadata", {}).get("heading", ""),
            "text": r.get("text", ""),
            "documentId": r.get("metadata", {}).get("document_id", ""),
            "pageNumber": (
                r.get("metadata", {}).get("start_page")
                or r.get("metadata", {}).get("page_number")
            ),
        }
        for r in reranked
    ]

    return {
        "answer": answer,
        "sources": sources,
        "pipelineDetails": {
            "method": "hybrid",
            "retrieved": len(retrieved),
            "reranked": len(reranked),
            "model": "gpt-4o-mini",
            "inputTokens": 0,
            "outputTokens": 0,
        },
    }
