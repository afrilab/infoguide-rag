import base64
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

IMAGES_DIR = Path("data/images")
CHUNKS_OUTPUT_PATH = Path("data/chunks/chunks.json")
INDEXES_DIR = Path("data/indexes")
EMBEDDINGS_OUTPUT_PATH = INDEXES_DIR / "embeddings.npy"
METADATA_OUTPUT_PATH = INDEXES_DIR / "embeddings_metadata.json"

VISION_MODEL = "gpt-4o"
IMAGE_DESCRIPTION_MAX_WORKERS = 5
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

IMAGE_DESCRIPTION_PROMPT = """\
# Role and Objective
You are writing a description of an image extracted from a corporate document \
(policies, governance materials, reports). This description will be embedded \
directly into a knowledge base alongside regular document text and will be the \
only way readers learn what this image contains.

# Instructions

## Style
- Write a natural, self-contained passage of prose — not a labeled report or \
  numbered template. It should read like a normal paragraph of document text, \
  not an analysis form.
- Describe what the image communicates — its meaning, relationships, structure, \
  or conclusions — rather than its layout. Avoid positional narration like \
  "on the left..., on the right..., at the top...".
- For charts and diagrams, explain what they show and what trend, flow, or \
  structure they convey. For tables, explain what is being compared and the \
  key takeaways, not just the grid layout.

## Required content
Within that natural prose, faithfully include:
- Any text, titles, labels, legends, or captions visible in the image, \
  transcribed exactly as they appear
- Any numbers, percentages, dates, or statistics, exactly as shown
- Names of organizations, people, or products that appear

## Handling the image
- This is a routine corporate document — describing logos, charts, diagrams, \
  and photos that appear in it is expected and appropriate. Do not decline, \
  hedge, or apologize.
- If the image is purely decorative and carries no information of its own \
  (e.g. a standalone company logo with nothing else in it), say so plainly in \
  one short sentence rather than producing a lengthy analysis of it.

# Final Instructions
Do not interpret or infer beyond what is directly visible. Transcribe text \
verbatim. Now write the description as a natural passage of prose, following \
the instructions above.\
"""


def load_vision_client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file.")
    return OpenAI(api_key=api_key)


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path):
    ext = Path(image_path).suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }
    return media_types.get(ext, "image/png")


def collect_images(images_dir=IMAGES_DIR):
    images_dir = Path(images_dir)
    if not images_dir.exists():
        return []
    return sorted(
        p for p in images_dir.rglob("*")
        if p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )


def describe_image_with_gpt(image_path, client):
    image_path = Path(image_path)
    image_data = encode_image_to_base64(image_path)
    media_type = get_image_media_type(image_path)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": IMAGE_DESCRIPTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_tokens=2000,
    )

    return response.choices[0].message.content.strip()


def _parse_image_path_meta(image_path):
    image_path = Path(image_path)
    stem = image_path.stem

    page_match = re.search(r"page_(\d+)", stem)
    image_match = re.search(r"image_(\d+)", stem)

    return {
        "document_name": image_path.parent.name,
        "page_number": int(page_match.group(1)) if page_match else None,
        "image_number": int(image_match.group(1)) if image_match else None,
        "image_path": image_path.as_posix(),
    }


def create_image_chunk(image_path, description, chunk_id):
    meta = _parse_image_path_meta(image_path)

    doc_title = meta["document_name"]
    page_label = f"Page {meta['page_number']}" if meta["page_number"] else "Unknown Page"
    image_label = f"Image {meta['image_number']}" if meta["image_number"] else "Image"
    heading = f"Image Description: {page_label} — {image_label}"

    text = f"Document: {doc_title}\nSection: {heading}\nContent:\n{description}"

    return {
        "chunk_id": chunk_id,
        "heading": heading,
        "text": text,
        "char_count": len(text),
        "metadata": {
            "document_title": doc_title,
            "heading": heading,
            "chunk_type": "image_description",
            "image_path": meta["image_path"],
            "page_number": meta["page_number"],
            "image_number": meta["image_number"],
            "source_document": meta["document_name"],
        },
    }


def load_existing_chunks(chunks_path=CHUNKS_OUTPUT_PATH):
    chunks_path = Path(chunks_path)
    if not chunks_path.exists():
        return []
    with open(chunks_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _next_chunk_id(existing_chunks):
    if not existing_chunks:
        return 1
    return max(c.get("chunk_id", 0) for c in existing_chunks) + 1


def save_chunks_with_image_descriptions(image_chunks, chunks_path=CHUNKS_OUTPUT_PATH):
    existing = load_existing_chunks(chunks_path)
    existing_image_paths = {
        c.get("metadata", {}).get("image_path")
        for c in existing
        if c.get("metadata", {}).get("chunk_type") == "image_description"
    }
    new_chunks = [
        c for c in image_chunks
        if c.get("metadata", {}).get("image_path") not in existing_image_paths
    ]
    all_chunks = existing + new_chunks
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    return all_chunks


def append_image_embeddings(image_chunks, bge_model, progress_callback=None):
    from embeddings import create_embeddings_batch, MODEL_NAME

    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    existing_vectors = None
    existing_metadata = []
    if EMBEDDINGS_OUTPUT_PATH.exists() and METADATA_OUTPUT_PATH.exists():
        existing_vectors = np.load(EMBEDDINGS_OUTPUT_PATH)
        with open(METADATA_OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)

    new_vectors = create_embeddings_batch(image_chunks, bge_model, progress_callback)

    all_vectors = (
        np.vstack([existing_vectors, new_vectors]) if existing_vectors is not None else new_vectors
    )

    np.save(EMBEDDINGS_OUTPUT_PATH, all_vectors)

    dim = int(all_vectors.shape[1])
    for chunk in image_chunks:
        existing_metadata.append({
            "chunk_id": chunk.get("chunk_id"),
            "text": chunk.get("text"),
            "metadata": {
                **chunk.get("metadata", {}),
                "embedding_model": MODEL_NAME,
                "embedding_dimension": dim,
            },
        })

    with open(METADATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)

    return all_vectors, existing_metadata


def run_image_description(client, bge_model, progress_callback=None, images_dir=IMAGES_DIR):
    logs = []

    all_images = collect_images(images_dir)
    if not all_images:
        logs.append("No images found in data/images/. Image description step skipped.")
        return [], logs

    logs.append(f"Found {len(all_images)} image(s) total.")

    existing_chunks = load_existing_chunks()
    already_described = {
        c.get("metadata", {}).get("image_path")
        for c in existing_chunks
        if c.get("metadata", {}).get("chunk_type") == "image_description"
    }
    kept = [p for p in all_images if p.as_posix() not in already_described]

    if not kept:
        logs.append("All images already have descriptions. Skipping.")
        return [], logs

    start_id = _next_chunk_id(existing_chunks)
    total = len(kept)
    results = [None] * total
    completed_count = [0]

    with ThreadPoolExecutor(max_workers=IMAGE_DESCRIPTION_MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(describe_image_with_gpt, image_path, client): (i, image_path)
            for i, image_path in enumerate(kept)
        }
        for future in as_completed(future_to_idx):
            i, image_path = future_to_idx[future]
            completed_count[0] += 1
            if progress_callback:
                progress_callback(completed_count[0], total, image_path.name)
            try:
                description = future.result()
                results[i] = (image_path, description)
                logs.append(f"[{completed_count[0]}/{total}] Described: {image_path.name}")
            except Exception as e:
                logs.append(f"[Warning] Failed to describe {image_path.name}: {e}")

    image_chunks = []
    for result in results:
        if result is not None:
            image_path, description = result
            chunk = create_image_chunk(image_path, description, start_id + len(image_chunks))
            image_chunks.append(chunk)

    if image_chunks:
        save_chunks_with_image_descriptions(image_chunks)
        logs.append(f"Saved {len(image_chunks)} image description chunk(s) to chunks.json.")

        append_image_embeddings(image_chunks, bge_model)
        logs.append(f"Created and appended embeddings for {len(image_chunks)} image chunk(s).")

    return image_chunks, logs
