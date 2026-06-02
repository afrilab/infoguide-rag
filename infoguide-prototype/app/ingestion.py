import re
from pathlib import Path

from docx import Document
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from pypdf import PdfReader

RAW_DATA_DIR = Path("data/raw")

MIN_MEANINGFUL_ALNUM_CHARS = 20
PDF_TEXT_X_TOLERANCE = 2
PDF_TEXT_Y_TOLERANCE = 2


def save_uploaded_file(uploaded_file):
    """
    Uploaded file'ı data/raw klasörüne kaydeder.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def clean_text(text):
    if text is None:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def clean_cell(cell):
    if cell is None:
        return ""

    value = str(cell).replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("\t", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.strip()
    return value.replace("|", "\\|")


def is_meaningful_text(text):
    cleaned = clean_text(text)
    if not cleaned:
        return False

    alnum_count = sum(char.isalnum() for char in cleaned)
    return alnum_count >= MIN_MEANINGFUL_ALNUM_CHARS


def normalize_table(table):
    if not table:
        return []

    normalized_rows = []

    for row in table:
        if row is None:
            continue

        cleaned_row = [clean_cell(cell) for cell in row]
        if any(cell for cell in cleaned_row):
            normalized_rows.append(cleaned_row)

    if not normalized_rows:
        return []

    column_count = max(len(row) for row in normalized_rows)
    return [row + [""] * (column_count - len(row)) for row in normalized_rows]


def looks_like_header(row):
    non_empty = [cell for cell in row if cell]
    if len(non_empty) < 2:
        return False

    unique_cells = len({cell.lower() for cell in non_empty})
    if unique_cells < 2:
        return False

    numeric_like = sum(
        1 for cell in non_empty
        if re.fullmatch(r"[\d.,\-%+\s]+", cell)
    )
    if numeric_like >= len(non_empty):
        return False

    return True


def dedupe_consecutive_rows(rows):
    if not rows:
        return []

    deduped = [rows[0]]
    for row in rows[1:]:
        if row != deduped[-1]:
            deduped.append(row)
    return deduped


def format_markdown_table(table):
    normalized_rows = normalize_table(table)
    if not normalized_rows:
        return ""

    normalized_rows = dedupe_consecutive_rows(normalized_rows)
    column_count = len(normalized_rows[0])

    if looks_like_header(normalized_rows[0]):
        header = normalized_rows[0]
        data_rows = normalized_rows[1:]
    else:
        header = [f"Column {index}" for index in range(1, column_count + 1)]
        data_rows = normalized_rows

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * column_count) + " |",
    ]

    for row in data_rows:
        if any(cell for cell in row):
            lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def extract_pdf_page_text(pdfplumber_page, pypdf_page, page_number):
    page_text = ""

    if pdfplumber_page is not None:
        try:
            page_text = pdfplumber_page.extract_text(
                layout=True,
                x_tolerance=PDF_TEXT_X_TOLERANCE,
                y_tolerance=PDF_TEXT_Y_TOLERANCE,
            )
        except Exception:
            page_text = ""

        if is_meaningful_text(page_text):
            return clean_text(page_text), "pdfplumber"

    if pypdf_page is not None:
        try:
            fallback_text = pypdf_page.extract_text() or ""
        except Exception:
            fallback_text = ""

        if is_meaningful_text(fallback_text):
            return clean_text(fallback_text), "pypdf"

    return "", "none"


def get_pdf_tables_from_page(pdfplumber_page):
    tables = []

    try:
        tables = pdfplumber_page.extract_tables() or []
    except Exception:
        tables = []

    if tables:
        return tables

    try:
        found_tables = pdfplumber_page.find_tables()
        for table in found_tables:
            try:
                extracted = table.extract()
                if extracted:
                    tables.append(extracted)
            except Exception:
                continue
    except Exception:
        return []

    return tables


def extract_pdf_page_tables(pdfplumber_page, page_number):
    rendered_tables = []

    try:
        tables = get_pdf_tables_from_page(pdfplumber_page)
    except Exception as e:
        return [f"[Warning: Table extraction failed on page {page_number}: {e}]"]

    for table_index, table in enumerate(tables, start=1):
        try:
            markdown_table = format_markdown_table(table)
            if not markdown_table.strip():
                continue

            rendered_tables.append(
                f"--- Page {page_number} Table {table_index} ---\n"
                f"[Table extracted from page {page_number}, table {table_index}]\n"
                f"{markdown_table}"
            )
        except Exception as e:
            rendered_tables.append(
                f"[Warning: Table extraction failed on page {page_number}: {e}]"
            )

    return rendered_tables


def run_ocr_for_page(file_path, page_number):
    images = convert_from_path(
        file_path,
        first_page=page_number,
        last_page=page_number,
    )

    ocr_text = pytesseract.image_to_string(images[0], lang="eng+tur")
    return clean_text(ocr_text)


def extract_text_from_pdf(file_path):
    """
    PDF dosyasından metin çıkarır.
    Sayfa bazlı selectable text + tablo extraction + OCR fallback.
    """
    output_parts = []

    reader = PdfReader(file_path)

    with pdfplumber.open(file_path) as pdf:
        total_pages = max(len(reader.pages), len(pdf.pages))

        for page_number in range(1, total_pages + 1):
            output_parts.append(f"--- Page {page_number} ---")

            try:
                pypdf_page = (
                    reader.pages[page_number - 1]
                    if page_number <= len(reader.pages)
                    else None
                )
                pdfplumber_page = (
                    pdf.pages[page_number - 1]
                    if page_number <= len(pdf.pages)
                    else None
                )

                if pdfplumber_page is None and pypdf_page is None:
                    output_parts.append(
                        f"[Warning: Text extraction failed on page {page_number}: page not found]"
                    )
                    continue

                page_text, _ = extract_pdf_page_text(
                    pdfplumber_page,
                    pypdf_page,
                    page_number,
                )

                if page_text:
                    output_parts.append(page_text)
                else:
                    try:
                        ocr_text = run_ocr_for_page(file_path, page_number)
                        if ocr_text:
                            output_parts.append(ocr_text)
                        else:
                            output_parts.append(
                                f"[Warning: OCR failed on page {page_number}: empty OCR output]"
                            )
                    except Exception as e:
                        output_parts.append(
                            f"[Warning: OCR failed on page {page_number}: {e}]"
                        )

                if pdfplumber_page is not None:
                    output_parts.extend(
                        extract_pdf_page_tables(pdfplumber_page, page_number)
                    )
            except Exception as e:
                output_parts.append(
                    f"[Warning: Text extraction failed on page {page_number}: {e}]"
                )

    return "\n\n".join(part for part in output_parts if part and part.strip())


def extract_text_from_txt(file_path):
    """
    TXT dosyasından metin çıkarır.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return content.replace("\r\n", "\n").replace("\r", "\n")


def docx_table_to_rows(table):
    rows = []
    for row in table.rows:
        rows.append([cell.text for cell in row.cells])
    return rows


def append_docx_table(text_parts, marker, table):
    text_parts.append(marker)
    try:
        markdown_table = format_markdown_table(docx_table_to_rows(table))
        if markdown_table:
            text_parts.append(markdown_table)
        else:
            text_parts.append("[Warning: Empty or invalid table]")
    except Exception as e:
        text_parts.append(f"[Warning: Table extraction failed: {e}]")


def extract_text_from_docx(file_path):
    """
    DOCX dosyasından paragraph, table, header ve footer metinlerini çıkarır.
    """
    doc = Document(file_path)
    text_parts = []

    text_parts.append("--- Document Paragraphs ---")
    try:
        for paragraph in doc.paragraphs:
            paragraph_text = clean_text(paragraph.text)
            if paragraph_text:
                text_parts.append(paragraph_text)
    except Exception as e:
        text_parts.append(f"[Warning: Document paragraph extraction failed: {e}]")

    for table_index, table in enumerate(doc.tables, start=1):
        append_docx_table(text_parts, f"--- Document Table {table_index} ---", table)

    for section_index, section in enumerate(doc.sections, start=1):
        text_parts.append(f"--- Section {section_index} Header ---")
        try:
            for paragraph in section.header.paragraphs:
                paragraph_text = clean_text(paragraph.text)
                if paragraph_text:
                    text_parts.append(paragraph_text)
        except Exception as e:
            text_parts.append(
                f"[Warning: Header extraction failed for section {section_index}: {e}]"
            )

        for table_index, table in enumerate(section.header.tables, start=1):
            append_docx_table(
                text_parts,
                f"--- Section {section_index} Header Table {table_index} ---",
                table,
            )

        text_parts.append(f"--- Section {section_index} Footer ---")
        try:
            for paragraph in section.footer.paragraphs:
                paragraph_text = clean_text(paragraph.text)
                if paragraph_text:
                    text_parts.append(paragraph_text)
        except Exception as e:
            text_parts.append(
                f"[Warning: Footer extraction failed for section {section_index}: {e}]"
            )

        for table_index, table in enumerate(section.footer.tables, start=1):
            append_docx_table(
                text_parts,
                f"--- Section {section_index} Footer Table {table_index} ---",
                table,
            )

    return "\n\n".join(part for part in text_parts if part and part.strip())


def extract_text(file_path):
    """
    Dosya uzantısına göre uygun text extraction fonksiyonunu çağırır.
    """
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".txt":
        return extract_text_from_txt(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError(f"Unsupported file type: {extension}")
