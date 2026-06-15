// To switch from mock to real backend: set VITE_USE_MOCK=false in .env
import * as mock from './mock/handlers'
import * as real from './real'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const api = USE_MOCK ? mock : real

export const ingestDocument = (file) => api.ingestDocument(file)
export const preprocessText = (rawText) => api.preprocessText(rawText)
export const chunkText = (cleanedText) => api.chunkText(cleanedText)
export const generateEmbeddings = (chunks) => api.generateEmbeddings(chunks)
export const describeImages = (chunks) => api.describeImages(chunks)
export const expandQuery = (query) => api.expandQuery(query)
export const decomposeQuery = (query) => api.decomposeQuery(query)
export const retrieveChunks = (params) => api.retrieveChunks(params)
export const rerankChunks = (params) => api.rerankChunks(params)
export const generateAnswer = (params) => api.generateAnswer(params)
export const processDocument = (file) => api.processDocument(file)
export const chatQuery = (params) => api.chatQuery(params)
export const deleteDocument = (documentId) => api.deleteDocument(documentId)
