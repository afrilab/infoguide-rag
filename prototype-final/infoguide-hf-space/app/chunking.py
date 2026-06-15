import json
import re
from pathlib import Path


PREPROCESSED_TEXT_PATH = Path("data/processed/preprocessed_text.txt")

CHUNKS_DIR = Path("data/chunks")
CHUNKS_OUTPUT_PATH = CHUNKS_DIR / "chunks.json"

MIN_CHUNK_CHARS = 300

DEFAULT_MAX_CHARS = 1800
DEFAULT_OVERLAP_CHARS = 250


def log_step(logs, message):
    logs.append(message)


def load_preprocessed_text(input_path=PREPROCESSED_TEXT_PATH):
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def is_page_marker(line):
    return bool(re.match(r"^---\s*Page\s+\d+\s*---$", line.strip(), re.IGNORECASE))


def extract_page_number(line):
    match = re.match(r"^---\s*Page\s+(\d+)\s*---$", line.strip(), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def is_table_marker(line):
    return bool(re.match(r"^---.*\bTable\s+\d+", line.strip(), re.IGNORECASE))


def get_heading_level(line):
    line = line.strip()

    md_match = re.match(r"^(#+)\s+", line)
    if md_match:
        return len(md_match.group(1))

    num_match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+", line)
    if num_match:
        return len(num_match.group(1).split("."))

    if re.match(r"^(Chapter|Section|CHAPTER|SECTION)\s+\d+", line, re.IGNORECASE):
        return 1

    return 1


def is_heading(line):
    line = line.strip()

    if not line:
        return False

    if is_page_marker(line):
        return False

    if is_table_marker(line):
        return False

    if len(line) < 3:
        return False

    if len(line) > 140:
        return False

    heading_patterns = [
        r"^\d+(\.\d+)*\.?\s+.+$",          # 1 Intro, 1. Intro, 2.1 Intro
        r"^(Chapter|Section)\s+\d+.*$",    # Chapter 1, Section 2
        r"^(CHAPTER|SECTION)\s+\d+.*$",    # CHAPTER 1, SECTION 2
        r"^#+\s+.+$",                      # Markdown headings
    ]

    for pattern in heading_patterns:
        if re.match(pattern, line):
            return True

    # ALL CAPS: harf sayısı rakam sayısından fazla olmalı (ISBN, sürüm numaraları vb. elenir)
    if re.match(r"^[A-ZÇĞİÖŞÜ0-9][A-ZÇĞİÖŞÜ0-9\s\-:()/]{4,}$", line):
        letter_count = sum(1 for c in line if c.isalpha())
        digit_count = sum(1 for c in line if c.isdigit())
        if letter_count > digit_count:
            return True

    return False


def get_overlap_text(text, overlap_chars):
    if not text or overlap_chars <= 0:
        return ""

    text = text.strip()

    if len(text) <= overlap_chars:
        return text

    overlap = text[-overlap_chars:]

    sentence_boundary = max(
        overlap.rfind(". "),
        overlap.rfind("? "),
        overlap.rfind("! ")
    )

    if sentence_boundary != -1:
        return overlap[sentence_boundary + 2:].strip()

    first_space = overlap.find(" ")
    if first_space != -1:
        return overlap[first_space + 1:].strip()

    return overlap.strip()


def split_long_paragraph(paragraph, max_chars, overlap_chars):
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)

    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""

            start = 0
            while start < len(sentence):
                end = start + max_chars
                part = sentence[start:end].strip()

                if part:
                    chunks.append(part)

                next_start = end - overlap_chars if overlap_chars > 0 else end

                if next_start <= start:
                    next_start = end

                start = next_start

            continue

        candidate = (current + " " + sentence).strip() if current else sentence

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())

            overlap = get_overlap_text(current, overlap_chars)
            current = (overlap + " " + sentence).strip() if overlap else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def split_text_recursive(text, max_chars, overlap_chars):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""

            chunks.extend(split_long_paragraph(paragraph, max_chars, overlap_chars))
            continue

        candidate = (current + "\n\n" + paragraph).strip() if current else paragraph

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())

            overlap = get_overlap_text(current, overlap_chars)
            current = (overlap + "\n\n" + paragraph).strip() if overlap else paragraph

    if current.strip():
        chunks.append(current.strip())

    return chunks



_ARTIFACT_PATTERNS = [
    re.compile(r"^--- Document Paragraphs ---$"),
    re.compile(r"^--- Extracted Images ---$"),
    re.compile(r"^--- Section \d+ (Header|Footer) ---$"),
    re.compile(r"^\[Table extracted"),
    re.compile(r"^\[Warning:"),
]


def _is_artifact_line(line):
    s = line.strip()
    return any(p.match(s) for p in _ARTIFACT_PATTERNS)


def _clean_image_marker(line):
    """data/images/... path'ini kısaltır, sadece page/image numarasını bırakır."""
    match = re.match(
        r"^\[Image extracted:[^|]+\|\s*(?:source=\w+\s*\|?\s*)?(?:page=(\d+)\s*\|?\s*)?image=(\d+)\]",
        line.strip(),
    )
    if match:
        page = match.group(1)
        img = match.group(2)
        return f"[Image: page={page}, image={img}]" if page else f"[Image: image={img}]"
    return line


def strip_extraction_artifacts(text):
    """Chunk içeriğine girmemesi gereken ingestion marker'larını temizler."""
    lines = []
    for line in text.splitlines():
        if _is_artifact_line(line):
            continue
        if line.strip().startswith("[Image extracted:"):
            lines.append(_clean_image_marker(line))
            continue
        lines.append(line)
    return "\n".join(lines)


def build_embedded_text(document_title, heading, content):
    parts = []

    if document_title:
        parts.append(f"Document: {document_title}")

    if heading and heading != "Document Start":
        parts.append(f"Section: {heading}")

    parts.append(f"Content:\n{content.strip()}")

    return "\n".join(parts)


def detect_document_title(text):
    """
    Detects a meaningful document title from the first part of the document.
    Avoids page numbers, metadata labels, table of contents lines, and very short numeric lines.
    """

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    bad_patterns = [
        r"^\d+\s*\(\d+\)$",                         # 1 (28)
        r"^page\s+\d+",                             # Page 1
        r"^adopted by",                             # Adopted by...
        r"^entry into force",                       # Entry into force...
        r"^version and adoption date",              # Version and adoption date...
        r"^document ownership",                     # Document ownership...
        r"^implementation responsibility",          # Implementation responsibility...
        r"^control responsibility",                 # Control responsibility...
        r"^review cycle",                           # Review cycle...
        r"^replaced document",                      # Replaced document...
        r"^table of contents",                      # Table of Contents
        r"^definitions$",                           # Definitions
    ]

    title_candidates = []

    for line in lines[:40]:
        lower_line = line.lower()

        if len(line) < 5:
            continue

        if len(line) > 120:
            continue

        if is_page_marker(line):
            continue

        if is_table_marker(line):
            continue

        if any(re.match(pattern, lower_line, re.IGNORECASE) for pattern in bad_patterns):
            continue

        # Prefer lines that look like document titles
        if any(keyword in lower_line for keyword in [
            "policy", "framework", "guideline", "procedure", "manual", "report",
            "politika", "yönetmelik", "yönerge", "rehber", "kılavuz",
            "prosedür", "rapor", "çerçeve", "standart", "talimat",
        ]):
            title_candidates.append(line)

    if title_candidates:
        # Prefer the shortest clean title-like candidate
        return sorted(title_candidates, key=len)[0]

    # Fallback: return first clean non-metadata line
    for line in lines[:40]:
        lower_line = line.lower()

        if len(line) < 5 or len(line) > 120:
            continue

        if is_page_marker(line):
            continue

        if is_table_marker(line):
            continue

        if any(re.match(pattern, lower_line, re.IGNORECASE) for pattern in bad_patterns):
            continue

        return line

    return "Uploaded Document"


def extract_sections(text):
    lines = text.splitlines()
    sections = []

    current_heading = "Document Start"
    current_breadcrumb = "Document Start"
    current_content = []
    current_page = None
    section_start_page = None

    heading_stack = []  # list of (level, heading_text)

    in_table = False
    table_heading = None
    table_breadcrumb = None
    table_content_lines = []
    table_start_page = None

    def _breadcrumb(stack, heading):
        if not stack:
            return heading
        return " > ".join([h for _, h in stack] + [heading])

    for line in lines:
        stripped = line.strip()

        page_number = extract_page_number(stripped)
        if page_number is not None:
            current_page = page_number
            continue

        if is_table_marker(stripped):
            if current_content:
                sections.append({
                    "heading": current_heading,
                    "breadcrumb": current_breadcrumb,
                    "content": "\n".join(current_content).strip(),
                    "start_page": section_start_page,
                    "end_page": current_page,
                    "chunk_type": "text",
                })
                current_content = []
                section_start_page = None
            if in_table and table_content_lines:
                sections.append({
                    "heading": table_heading,
                    "breadcrumb": table_breadcrumb,
                    "content": "\n".join(table_content_lines).strip(),
                    "start_page": table_start_page,
                    "end_page": current_page,
                    "chunk_type": "table",
                })
                table_content_lines = []
            in_table = True
            table_heading = stripped
            table_breadcrumb = _breadcrumb(heading_stack, stripped)
            table_start_page = current_page
            continue

        if in_table:
            if stripped.startswith("|"):
                table_content_lines.append(stripped)
                continue
            if table_content_lines:
                sections.append({
                    "heading": table_heading,
                    "breadcrumb": table_breadcrumb,
                    "content": "\n".join(table_content_lines).strip(),
                    "start_page": table_start_page,
                    "end_page": current_page,
                    "chunk_type": "table",
                })
            table_content_lines = []
            table_heading = None
            table_breadcrumb = None
            in_table = False

        if not stripped:
            current_content.append("")
            continue

        if is_heading(stripped):
            if current_content:
                sections.append({
                    "heading": current_heading,
                    "breadcrumb": current_breadcrumb,
                    "content": "\n".join(current_content).strip(),
                    "start_page": section_start_page,
                    "end_page": current_page,
                    "chunk_type": "text",
                })

            level = get_heading_level(stripped)
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()

            current_breadcrumb = _breadcrumb(heading_stack, stripped)
            heading_stack.append((level, stripped))

            current_heading = stripped
            current_content = []
            section_start_page = current_page
            continue

        if section_start_page is None:
            section_start_page = current_page
        current_content.append(stripped)

    if in_table and table_content_lines:
        sections.append({
            "heading": table_heading,
            "breadcrumb": table_breadcrumb,
            "content": "\n".join(table_content_lines).strip(),
            "start_page": table_start_page,
            "end_page": current_page,
            "chunk_type": "table",
        })
    if current_content:
        sections.append({
            "heading": current_heading,
            "breadcrumb": current_breadcrumb,
            "content": "\n".join(current_content).strip(),
            "start_page": section_start_page,
            "end_page": current_page,
            "chunk_type": "text",
        })

    return [s for s in sections if s.get("content", "").strip()]


def _extract_raw_content(embedded_text):
    marker = "Content:\n"
    idx = embedded_text.find(marker)
    if idx != -1:
        return embedded_text[idx + len(marker):]
    return embedded_text


def merge_small_chunks(chunks, min_chars=MIN_CHUNK_CHARS):
    if not chunks:
        return []

    merged = []

    for chunk in chunks:
        if not merged:
            merged.append(chunk)
            continue

        previous = merged[-1]
        previous_text = previous["text"]
        current_text = chunk["text"]

        same_section = (
            previous["metadata"].get("section_index") == chunk["metadata"].get("section_index")
        )

        max_chars = previous["metadata"].get("max_chunk_chars", DEFAULT_MAX_CHARS)

        is_table = (
            previous["metadata"].get("chunk_type") == "table_chunk"
            or chunk["metadata"].get("chunk_type") == "table_chunk"
        )

        if len(previous_text) < min_chars and same_section and not is_table:
            prev_content = _extract_raw_content(previous_text).strip()
            curr_content = _extract_raw_content(current_text).strip()
            merged_text = build_embedded_text(
                previous["metadata"].get("document_title"),
                previous["metadata"].get("section_breadcrumb") or previous["metadata"].get("heading"),
                prev_content + "\n\n" + curr_content,
            )
            if len(merged_text) <= max_chars:
                previous["text"] = merged_text
                previous["char_count"] = len(merged_text)
                previous["metadata"]["end_page"] = chunk["metadata"].get("end_page")
                previous["metadata"]["merged_small_chunk"] = True
                continue

        merged.append(chunk)

    for index, chunk in enumerate(merged, start=1):
        chunk["chunk_id"] = index

    return merged


def chunk_text(text):
    logs = []

    text = strip_extraction_artifacts(text)
    document_title = detect_document_title(text)
    sections = extract_sections(text)

    log_step(logs, "Step 1: Using Recommended Chunking configuration.")
    log_step(logs, f"Step 2: Detected document title: {document_title}")
    log_step(logs, f"Step 3: Detected {len(sections)} content sections.")

    chunks = []
    chunk_id = 1

    for section_index, section in enumerate(sections, start=1):
        heading = section["heading"]
        content = section["content"]
        section_type = section.get("chunk_type", "text")

        breadcrumb = section.get("breadcrumb", heading)

        if section_type == "table":
            final_text = build_embedded_text(
                document_title=document_title,
                heading=breadcrumb,
                content=content,
            )
            chunks.append({
                "chunk_id": chunk_id,
                "heading": heading,
                "text": final_text,
                "char_count": len(final_text),
                "metadata": {
                    "document_title": document_title,
                    "heading": heading,
                    "section_breadcrumb": breadcrumb,
                    "section_index": section_index,
                    "sub_chunk_id": 1,
                    "start_page": section.get("start_page"),
                    "end_page": section.get("end_page"),
                    "chunk_type": "table_chunk",
                    "chunking_strategy": "Recommended",
                    "max_chunk_chars": DEFAULT_MAX_CHARS,
                    "chunk_overlap_chars": DEFAULT_OVERLAP_CHARS,
                    "use_recursive": False,
                },
            })
            chunk_id += 1
            continue

        sub_chunks = split_text_recursive(
            content,
            max_chars=DEFAULT_MAX_CHARS,
            overlap_chars=DEFAULT_OVERLAP_CHARS,
        )

        for sub_index, sub_chunk in enumerate(sub_chunks, start=1):
            final_text = build_embedded_text(
                document_title=document_title,
                heading=breadcrumb,
                content=sub_chunk,
            )
            chunks.append({
                "chunk_id": chunk_id,
                "heading": heading,
                "text": final_text,
                "char_count": len(final_text),
                "metadata": {
                    "document_title": document_title,
                    "heading": heading,
                    "section_breadcrumb": breadcrumb,
                    "section_index": section_index,
                    "sub_chunk_id": sub_index,
                    "start_page": section.get("start_page"),
                    "end_page": section.get("end_page"),
                    "chunk_type": "chunk",
                    "chunking_strategy": "Recommended",
                    "max_chunk_chars": DEFAULT_MAX_CHARS,
                    "chunk_overlap_chars": DEFAULT_OVERLAP_CHARS,
                    "use_recursive": True,
                },
            })
            chunk_id += 1

    chunks = merge_small_chunks(chunks)

    log_step(logs, f"Step 4: Created {len(chunks)} searchable child chunks.")
    log_step(logs, f"Step 5: Max chunk size: {DEFAULT_MAX_CHARS} characters.")
    log_step(logs, f"Step 6: Overlap size: {DEFAULT_OVERLAP_CHARS} characters.")
    log_step(logs, "Step 7: Recursive splitting is enabled.")

    return chunks, logs



def save_chunks(chunks, output_path=CHUNKS_OUTPUT_PATH):
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    return output_path


def run_chunking(input_path=PREPROCESSED_TEXT_PATH):
    text = load_preprocessed_text(input_path)

    chunks, logs = chunk_text(text)

    chunks_output_path = save_chunks(chunks)

    logs.append(f"Step 8: Chunks saved to {chunks_output_path}")

    return chunks, logs, chunks_output_path


if __name__ == "__main__":
    chunks, logs, output_path = run_chunking()

    for log in logs:
        print(log)

    print(f"\nOutput file: {output_path}")