import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

RAW_DATA_DIR = Path("data/raw")


def save_uploaded_file(uploaded_file):
    """
    Uploaded file'ı data/raw klasörüne kaydeder.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def extract_text_from_pdf(file_path):
    """
    PDF dosyasından metin çıkarır.
    Önce selectable text çıkarır.
    Eğer sayfada metin yoksa sadece o sayfa için OCR yapar.
    Ayrıca tabloları da çıkarır.
    """
    text = ""

    reader = PdfReader(file_path)

    with pdfplumber.open(file_path) as pdf:
        for page_number, page in enumerate(reader.pages, start=1):
            text += f"\n\n--- Page {page_number} ---\n"

            page_text = page.extract_text()

            if page_text and page_text.strip():
                text += page_text.strip() + "\n"
            else:
                text += "[No selectable text found. OCR used.]\n"

                images = convert_from_path(
                    file_path,
                    first_page=page_number,
                    last_page=page_number
                )

                ocr_text = pytesseract.image_to_string(
                    images[0],
                    lang="eng+tur"
                )

                if ocr_text.strip():
                    text += ocr_text.strip() + "\n"

            # Same page tables
            plumber_page = pdf.pages[page_number - 1]
            tables = plumber_page.extract_tables()

            if tables:
                text += f"\n--- Page {page_number} Tables ---\n"

                for table_index, table in enumerate(tables, start=1):
                    text += f"\nTable {table_index}:\n"

                    for row in table:
                        cleaned_row = [
                            cell.strip() if cell else ""
                            for cell in row
                        ]
                        text += " | ".join(cleaned_row) + "\n"

    return text

def extract_text_from_txt(file_path):
    """
    TXT dosyasından metin çıkarır.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text_from_docx(file_path):
    """
    DOCX dosyasından paragraph, table, header ve footer metinlerini çıkarır.
    """
    doc = Document(file_path)
    text = ""

    # Main paragraphs
    text += "\n--- Document Paragraphs ---\n"
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text.strip() + "\n"

    # Main tables
    for table_index, table in enumerate(doc.tables, start=1):
        text += f"\n--- Table {table_index} ---\n"

        for row in table.rows:
            row_cells = []

            for cell in row.cells:
                cell_text = cell.text.strip()
                row_cells.append(cell_text)

            text += " | ".join(row_cells) + "\n"

    # Headers and footers
    for section_index, section in enumerate(doc.sections, start=1):
        # Header paragraphs
        text += f"\n--- Section {section_index} Header ---\n"
        for paragraph in section.header.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text.strip() + "\n"

        # Header tables
        for table_index, table in enumerate(section.header.tables, start=1):
            text += f"\n--- Section {section_index} Header Table {table_index} ---\n"

            for row in table.rows:
                row_cells = []

                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_cells.append(cell_text)

                text += " | ".join(row_cells) + "\n"

        # Footer paragraphs
        text += f"\n--- Section {section_index} Footer ---\n"
        for paragraph in section.footer.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text.strip() + "\n"

        # Footer tables
        for table_index, table in enumerate(section.footer.tables, start=1):
            text += f"\n--- Section {section_index} Footer Table {table_index} ---\n"

            for row in table.rows:
                row_cells = []

                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_cells.append(cell_text)

                text += " | ".join(row_cells) + "\n"

    return text


def extract_text(file_path):
    """
    Dosya uzantısına göre uygun text extraction fonksiyonunu çağırır.
    """
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    elif extension == ".txt":
        return extract_text_from_txt(file_path)

    elif extension == ".docx":
        return extract_text_from_docx(file_path)

    else:
        raise ValueError(f"Unsupported file type: {extension}")