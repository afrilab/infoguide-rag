import re
from collections import Counter


def log_step(logs, message):
    logs.append(message)


def clean_invisible_chars(text):
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\u00ad", "")   # soft hyphen
    text = text.replace("\u2028", "\n") # line separator
    text = text.replace("\u2029", "\n") # paragraph separator
    return text


def fix_hyphenated_words(text):
    return re.sub(r"(\w)- ?\n(\w)", r"\1\2", text)


def normalize_line_breaks(text):
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if line:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append("")

    return "\n".join(cleaned_lines)


def normalize_spaces(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_repeated_headers_footers(text):
    """
    Çok sık tekrar eden kısa satırları siler.
    Page markerları korunur.
    """
    lines = text.splitlines()

    candidates = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("--- Page")
        and not line.strip().startswith("|")
        and not line.strip().startswith("---")
        and not line.strip().startswith("[")
        and len(line.strip()) < 80
    ]

    counts = Counter(candidates)

    repeated_lines = {
        line for line, count in counts.items()
        if count >= 3 and len(line) < 50
    }

    cleaned = []

    for line in lines:
        stripped = line.strip()

        if stripped in repeated_lines:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def preprocess_text(text):
    logs = []

    log_step(logs, "Step 1: Cleaning invisible characters...")
    text = clean_invisible_chars(text)

    log_step(logs, "Step 2: Fixing hyphenated words split across lines...")
    text = fix_hyphenated_words(text)

    log_step(logs, "Step 3: Normalizing line breaks...")
    text = normalize_line_breaks(text)

    log_step(logs, "Step 4: Removing repeated headers and footers...")
    text = remove_repeated_headers_footers(text)

    log_step(logs, "Step 5: Normalizing extra spaces and blank lines...")
    text = normalize_spaces(text)

    log_step(logs, "Preprocessing completed successfully.")

    return text, logs