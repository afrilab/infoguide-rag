import base64
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from openai import OpenAI
from dotenv import load_dotenv
import os

IMAGES_DIR = Path("data/images")
CHUNKS_OUTPUT_PATH = Path("data/chunks/chunks.json")
INDEXES_DIR = Path("data/indexes")
EMBEDDINGS_OUTPUT_PATH = INDEXES_DIR / "embeddings.npy"
METADATA_OUTPUT_PATH = INDEXES_DIR / "embeddings_metadata.json"

MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100
MIN_PIXEL_AREA = 15000   # ~122x122 minimum
MIN_STD_DEV = 8.0        # below this = blank/near-uniform image

VISION_MODEL = "gpt-4o"
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

IMAGE_DESCRIPTION_PROMPT = (
    "Please provide a comprehensive and detailed description of this image. "
    "Include: what the image shows, any visible text, charts or diagrams and their content, "
    "tables and their data, logos or visual identifiers, and any other information "
    "that would help someone understand this image without seeing it. "
    "Be thorough — this description will be used for information retrieval."
)


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


def is_meaningful_image(image_path):
    """Returns (is_meaningful: bool, reason: str).

    Filters out:
    - Images smaller than MIN_IMAGE_WIDTH x MIN_IMAGE_HEIGHT
    - Near-blank or near-uniform images (black screens, white pages, decorative rules)
    """
    try:
        with PILImage.open(image_path) as img:
            w, h = img.size

            if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
                return False, f"too small ({w}x{h} px)"

            if w * h < MIN_PIXEL_AREA:
                return False, f"area too small ({w * h} px²)"

            gray = img.convert("L")
            arr = np.array(gray, dtype=np.float32)
            std = float(arr.std())

            if std < MIN_STD_DEV:
                return False, f"blank/uniform image (std={std:.1f})"

            return True, "ok"

    except Exception as e:
        return False, f"could not open: {e}"


def filter_meaningful_images(images):
    """Returns (kept: list[Path], skipped: list[tuple[Path, str]])."""
    kept = []
    skipped = []
    for path in images:
        ok, reason = is_meaningful_image(path)
        if ok:
            kept.append(path)
        else:
            skipped.append((path, reason))
    return kept, skipped


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
        max_tokens=1000,
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


def create_image_chunk(image_path, description, chunk_id, document_title=None):
    meta = _parse_image_path_meta(image_path)

    doc_title = document_title or meta["document_name"]
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


def _existing_doc_title(existing_chunks):
    if not existing_chunks:
        return None
    return existing_chunks[0].get("metadata", {}).get("document_title")


def save_chunks_with_image_descriptions(image_chunks, chunks_path=CHUNKS_OUTPUT_PATH):
    existing = load_existing_chunks(chunks_path)
    all_chunks = existing + image_chunks
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    return all_chunks


def append_image_embeddings(image_chunks, bge_model, progress_callback=None):
    from embeddings import create_embeddings_one_by_one, MODEL_NAME

    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    existing_vectors = (
        np.load(EMBEDDINGS_OUTPUT_PATH) if EMBEDDINGS_OUTPUT_PATH.exists() else None
    )

    existing_metadata = []
    if METADATA_OUTPUT_PATH.exists():
        with open(METADATA_OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)

    new_vectors = create_embeddings_one_by_one(image_chunks, bge_model, progress_callback)

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

    kept, skipped = filter_meaningful_images(all_images)

    for path, reason in skipped:
        logs.append(f"  Skipped {path.name}: {reason}")

    logs.append(f"{len(kept)} image(s) passed filtering, {len(skipped)} skipped.")

    if not kept:
        logs.append("No meaningful images to describe after filtering.")
        return [], logs

    existing_chunks = load_existing_chunks()
    start_id = _next_chunk_id(existing_chunks)
    doc_title = _existing_doc_title(existing_chunks)

    image_chunks = []

    for index, image_path in enumerate(kept, start=1):
        if progress_callback:
            progress_callback(index, len(kept), image_path.name)

        try:
            description = describe_image_with_gpt(image_path, client)
            chunk = create_image_chunk(image_path, description, start_id + index - 1, doc_title)
            image_chunks.append(chunk)
            logs.append(f"[{index}/{len(kept)}] Described: {image_path.name}")
        except Exception as e:
            logs.append(f"[Warning] Failed to describe {image_path.name}: {e}")

    if image_chunks:
        save_chunks_with_image_descriptions(image_chunks)
        logs.append(f"Saved {len(image_chunks)} image description chunk(s) to chunks.json.")

        append_image_embeddings(image_chunks, bge_model)
        logs.append(f"Created and appended embeddings for {len(image_chunks)} image chunk(s).")

    return image_chunks, logs
