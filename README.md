# InfoGuide RAG

InfoGuide is a **Retrieval-Augmented Generation (RAG)** application that answers questions over corporate documents (PDF, DOCX, TXT) and cites its sources. The repo contains two main parts: a FastAPI backend (the RAG pipeline) and a React (Vite) chat interface.

```
infoguide-rag/
├── infoguide-prototype/   ← Backend: RAG pipeline + FastAPI service
└── infoguide-frontend/    ← Frontend: React-based chat interface
```

---

## Architecture

```
Document Upload
      ↓
  Ingestion          ← extract text, tables, and images
      ↓
 Preprocessing       ← clean and normalize text
      ↓
   Chunking          ← split by heading, isolate tables, build breadcrumbs
      ↓
  Embedding          ← vectorize with BGE-M3
      ↓
Image Description    ← generate image chunks with GPT-4o Vision
      ↓
Query Expansion      ← expand and decompose the query into sub-queries with GPT-4o-mini
      ↓
  Retrieval          ← hybrid FAISS + BM25, multi-query RRF
      ↓
  Reranking          ← BGE-reranker-v2-m3 cross-encoder
      ↓
  Generation         ← produce the answer and cite sources with GPT-4o-mini
      ↓
   Chat UI           ← React interface showing the answer, sources, and document navigation
```

For a detailed breakdown of the backend components (ingestion, chunking, embedding, retrieval, reranking, generation, etc.), see **[infoguide-prototype/README.md](infoguide-prototype/README.md)**.

---

## Models

| Task | Model |
|------|-------|
| Embedding | `BAAI/bge-m3` |
| Reranking | `BAAI/bge-reranker-v2-m3` |
| Query Expansion, Decomposition & Generation | `gpt-4o-mini` |
| Image Description | `gpt-4o` |

## Tech Stack

| Layer | Library / Tool |
|-------|----------------|
| Backend API | FastAPI, Uvicorn |
| PDF/DOCX extraction | pdfplumber, pypdf, PyMuPDF (fitz), python-docx |
| OCR | pdf2image, pytesseract |
| Embedding & Reranking | sentence-transformers, LangChain HuggingFace Embeddings |
| Vector / keyword search | faiss-cpu, rank-bm25 |
| LLM | OpenAI API (`gpt-4o`, `gpt-4o-mini`) |
| Frontend | React, Vite, Tailwind CSS, react-markdown |

---

## Setup and Running

### Backend (`infoguide-prototype`)

```bash
cd infoguide-prototype
pip install -r requirements.txt
```

Create a `.env` file in the `app/` directory with your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

Start the server:

```bash
cd app
uvicorn server:app --reload
```

The backend runs at `http://localhost:8000` by default.

### Frontend (`infoguide-frontend`)

```bash
cd infoguide-frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` by default and connects to the backend at `http://localhost:8000`.

---

## Usage

1. Upload a document (PDF, DOCX, or TXT) from the frontend — the backend processes and indexes it (ingestion → chunking → embedding → image description).
2. Ask a question about the document from the chat screen.
3. The system finds the most relevant sections via hybrid retrieval (FAISS + BM25) and reranking, generates an answer from them, and shows the source chunks.
4. Click on a source to jump to the relevant page in the original document.
