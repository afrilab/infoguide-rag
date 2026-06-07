// Real API implementation — swap in by setting VITE_USE_MOCK=false in .env

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const post = async (path, body) => {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

const postForm = async (path, formData) => {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

export const ingestDocument = async (file) => {
  const form = new FormData()
  form.append('file', file)
  return postForm('/ingest', form)
}

export const preprocessText = async (rawText) =>
  post('/preprocess', { raw_text: rawText })

export const chunkText = async (cleanedText) =>
  post('/chunk', { cleaned_text: cleanedText })

export const generateEmbeddings = async (chunks) =>
  post('/embed', { chunks })

export const describeImages = async (chunks) =>
  post('/describe-images', { chunks })

export const expandQuery = async (query) =>
  post('/expand-query', { query })

export const decomposeQuery = async (query) =>
  post('/decompose-query', { query })

export const retrieveChunks = async ({ query, expandedQuery, method, topK }) =>
  post('/retrieve', { query, expanded_query: expandedQuery, method, top_k: topK })

export const rerankChunks = async ({ query, chunks, topK }) =>
  post('/rerank', { query, chunks, top_k: topK })

export const generateAnswer = async ({ query, chunks }) =>
  post('/generate', { query, chunks })

// Backend must return: { pageCount, chunkCount, documentId }
// documentId is the backend's stable ID for this document — returned in chatQuery source objects.
export const processDocument = async (file) => {
  const form = new FormData()
  form.append('file', file)
  return postForm('/chat/process', form)
}

// Backend must return sources as: { chunkId, heading, text, documentId, pageNumber }
// documentId must match the id returned by /chat/process; pageNumber is 1-indexed.
export const chatQuery = async ({ query, documentIds }) =>
  post('/chat/query', { query, document_ids: documentIds })
