FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for PDF processing, images, OCR fallback, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY app/ ./app/
COPY prompts/ ./prompts/

# Create data directories for persistence
RUN mkdir -p data/raw data/chunks data/indexes data/images data/processed

# Expose port (HF Spaces uses 7860 by default)
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]
