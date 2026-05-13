import json
import re
from pathlib import Path


PREPROCESSED_TEXT_PATH = Path("data/processed/preprocessed_text.txt")

CHUNKS_DIR = Path("data/chunks")
CHUNKS_OUTPUT_PATH = CHUNKS_DIR / "chunks.json"

MIN_CHUNK_CHARS = 300
MAX_CHUNK_CHARS = 1500


def log_step(logs, message):
    logs.append(message)


def load_preprocessed_text(input_path=PREPROCESSED_TEXT_PATH):
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def is_heading(line):
    line = line.strip()

    if len(line) < 3:
        return False

    if len(line) > 120:
        return False

    heading_patterns = [
        r"^\d+(\.\d+)*\s+.+$",                 # 1 Introduction, 2.1 Method
        r"^(Chapter|Section)\s+\d+.*$",        # Chapter 1, Section 2
        r"^(CHAPTER|SECTION)\s+\d+.*$",        # CHAPTER 1
        r"^#+\s+.+$",                          # Markdown headings
        r"^[A-ZÇĞİÖŞÜ0-9][A-ZÇĞİÖŞÜ0-9\s\-:]{3,}$",  # ALL CAPS
    ]

    for pattern in heading_patterns:
        if re.match(pattern, line):
            return True

    return False


def split_long_text(text, max_chars=MAX_CHUNK_CHARS):
    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current_chunk) + len(paragraph) <= max_chars:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def heading_based_chunk_text(text):
    logs = []
    log_step(logs, "Step 1: Starting heading-based chunking...")

    lines = text.splitlines()

    sections = []
    current_heading = "Document Start"
    current_content = []

    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            current_content.append("")
            continue

        if is_heading(stripped_line):
            if current_content:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_content).strip()
                })

            current_heading = stripped_line
            current_content = []
        else:
            current_content.append(stripped_line)

    if current_content:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_content).strip()
        })

    log_step(logs, f"Step 2: Detected {len(sections)} heading sections.")

    chunks = []
    chunk_id = 1

    for section in sections:
        heading = section["heading"]
        content = section["content"]

        if not content:
            continue

        if len(content) <= MAX_CHUNK_CHARS:
            chunks.append({
                "chunk_id": chunk_id,
                "heading": heading,
                "text": content,
                "char_count": len(content)
            })
            chunk_id += 1
        else:
            sub_chunks = split_long_text(content)

            for sub_index, sub_chunk in enumerate(sub_chunks, start=1):
                chunks.append({
                    "chunk_id": chunk_id,
                    "heading": heading,
                    "sub_chunk_id": sub_index,
                    "text": sub_chunk,
                    "char_count": len(sub_chunk)
                })
                chunk_id += 1

    log_step(logs, f"Step 3: Created {len(chunks)} chunks.")

    return chunks, logs


def save_chunks(chunks, output_path=CHUNKS_OUTPUT_PATH):
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    return output_path


def run_chunking(input_path=PREPROCESSED_TEXT_PATH):
    text = load_preprocessed_text(input_path)

    chunks, logs = heading_based_chunk_text(text)

    output_path = save_chunks(chunks)

    logs.append(f"Step 4: Chunks saved to {output_path}")

    return chunks, logs, output_path


if __name__ == "__main__":
    chunks, logs, output_path = run_chunking()

    for log in logs:
        print(log)

    print(f"\nOutput file: {output_path}")