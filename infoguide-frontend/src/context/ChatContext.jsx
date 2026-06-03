import { createContext, useContext, useReducer, useRef, useEffect } from 'react'
import { processDocument, chatQuery } from '../api/index'

const initialState = {
  documents: [],
  messages: [],
  isProcessingDoc: false,
  isGenerating: false,
}

function reducer(state, action) {
  switch (action.type) {
    case 'ADD_DOCUMENT':
      return {
        ...state,
        isProcessingDoc: true,
        documents: [...state.documents, action.doc],
      }
    case 'DOCUMENT_READY':
      return {
        ...state,
        isProcessingDoc: false,
        documents: state.documents.map((d) =>
          d.id === action.id
            ? { ...d, status: 'ready', pageCount: action.pageCount, chunkCount: action.chunkCount }
            : d
        ),
      }
    case 'DOCUMENT_ERROR':
      return {
        ...state,
        isProcessingDoc: false,
        documents: state.documents.map((d) =>
          d.id === action.id ? { ...d, status: 'error' } : d
        ),
      }
    case 'REMOVE_DOCUMENT':
      return { ...state, documents: state.documents.filter((d) => d.id !== action.id) }
    case 'ADD_USER_MESSAGE':
      return { ...state, isGenerating: true, messages: [...state.messages, action.message] }
    case 'ADD_ASSISTANT_MESSAGE':
      return { ...state, isGenerating: false, messages: [...state.messages, action.message] }
    case 'GENERATION_ERROR':
      return { ...state, isGenerating: false }
    default:
      return state
  }
}

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const stateRef = useRef(state)
  useEffect(() => { stateRef.current = state }, [state])

  const addDocument = async (file) => {
    const id = `doc_${Date.now()}`
    dispatch({
      type: 'ADD_DOCUMENT',
      doc: { id, name: file.name, size: file.size, status: 'ingesting', pageCount: 0, chunkCount: 0 },
    })
    try {
      const result = await processDocument(file)
      dispatch({ type: 'DOCUMENT_READY', id, pageCount: result.pageCount, chunkCount: result.chunkCount })
    } catch {
      dispatch({ type: 'DOCUMENT_ERROR', id })
    }
  }

  const removeDocument = (id) => dispatch({ type: 'REMOVE_DOCUMENT', id })

  const sendMessage = async (query) => {
    const userMsg = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    }
    dispatch({ type: 'ADD_USER_MESSAGE', message: userMsg })
    try {
      const docIds = stateRef.current.documents.filter((d) => d.status === 'ready').map((d) => d.id)
      const result = await chatQuery({ query, documentIds: docIds })
      dispatch({
        type: 'ADD_ASSISTANT_MESSAGE',
        message: {
          id: `msg_${Date.now()}_ai`,
          role: 'assistant',
          content: result.answer,
          sources: result.sources,
          pipelineDetails: result.pipelineDetails,
          timestamp: new Date(),
        },
      })
    } catch {
      dispatch({ type: 'GENERATION_ERROR' })
    }
  }

  return (
    <ChatContext.Provider value={{ ...state, addDocument, removeDocument, sendMessage }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useChat = () => {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside ChatProvider')
  return ctx
}
