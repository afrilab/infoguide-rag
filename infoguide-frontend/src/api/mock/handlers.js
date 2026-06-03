import {
  MOCK_INGESTION,
  MOCK_PREPROCESSING,
  MOCK_CHUNKS,
  MOCK_EMBEDDING,
  MOCK_IMAGE_DESCRIPTION,
  MOCK_QUERY_EXPANSION,
  MOCK_RETRIEVAL,
  MOCK_RERANKING,
  MOCK_GENERATION,
  MOCK_CHAT_RESPONSE,
} from './data'

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

export const ingestDocument = async (_file) => {
  await delay(1800)
  return { ...MOCK_INGESTION }
}

export const preprocessText = async (_rawText) => {
  await delay(1200)
  return { ...MOCK_PREPROCESSING }
}

export const chunkText = async (_cleanedText) => {
  await delay(900)
  return { ...MOCK_CHUNKS }
}

export const generateEmbeddings = async (_chunks) => {
  await delay(2500)
  return { ...MOCK_EMBEDDING }
}

export const describeImages = async (_chunks) => {
  await delay(3000)
  return { ...MOCK_IMAGE_DESCRIPTION }
}

export const expandQuery = async (_query) => {
  await delay(1400)
  return { ...MOCK_QUERY_EXPANSION }
}

export const retrieveChunks = async (_params) => {
  await delay(800)
  return { ...MOCK_RETRIEVAL, method: _params?.method ?? 'hybrid', topK: _params?.topK ?? 5 }
}

export const rerankChunks = async (_params) => {
  await delay(1600)
  return { ...MOCK_RERANKING, topK: _params?.topK ?? 3 }
}

export const generateAnswer = async (_params) => {
  await delay(2200)
  return { ...MOCK_GENERATION }
}

export const processDocument = async (_file) => {
  await delay(2800)
  return { pageCount: 42, chunkCount: 11 }
}

export const chatQuery = async (_params) => {
  await delay(2400)
  return { ...MOCK_CHAT_RESPONSE }
}
