import { createContext, useContext, useReducer, useRef, useEffect } from 'react'
import { processDocument, chatQuery } from '../api/index'

function makeChat(id) {
  return { id, title: 'New Chat', messages: [], documents: [], isProcessingDoc: false, isGenerating: false }
}

const firstId = `chat_${Date.now()}`

const initialState = {
  chats: [makeChat(firstId)],
  activeChatId: firstId,
}

function updateChat(chats, id, updater) {
  return chats.map((c) => (c.id === id ? updater(c) : c))
}

function reducer(state, action) {
  switch (action.type) {
    case 'CREATE_CHAT': {
      return { chats: [...state.chats, makeChat(action.id)], activeChatId: action.id }
    }
    case 'SELECT_CHAT':
      return { ...state, activeChatId: action.id }
    case 'ADD_DOCUMENT':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          isProcessingDoc: true,
          documents: [...c.documents, action.doc],
        })),
      }
    case 'DOCUMENT_READY':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          isProcessingDoc: false,
          documents: c.documents.map((d) =>
            d.id === action.id
              ? { ...d, status: 'ready', pageCount: action.pageCount, chunkCount: action.chunkCount, backendId: action.backendId }
              : d
          ),
        })),
      }
    case 'DOCUMENT_ERROR':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          isProcessingDoc: false,
          documents: c.documents.map((d) =>
            d.id === action.id ? { ...d, status: 'error' } : d
          ),
        })),
      }
    case 'REMOVE_DOCUMENT':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          documents: c.documents.filter((d) => d.id !== action.id),
        })),
      }
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          isGenerating: true,
          title: c.messages.length === 0
            ? action.message.content.slice(0, 28) + (action.message.content.length > 28 ? '…' : '')
            : c.title,
          messages: [...c.messages, action.message],
        })),
      }
    case 'ADD_ASSISTANT_MESSAGE':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({
          ...c,
          isGenerating: false,
          messages: [...c.messages, action.message],
        })),
      }
    case 'GENERATION_ERROR':
      return {
        ...state,
        chats: updateChat(state.chats, action.chatId, (c) => ({ ...c, isGenerating: false })),
      }
    default:
      return state
  }
}

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const stateRef = useRef(state)
  useEffect(() => { stateRef.current = state }, [state])

  const createChat = () => {
    dispatch({ type: 'CREATE_CHAT', id: `chat_${Date.now()}` })
  }

  const selectChat = (id) => dispatch({ type: 'SELECT_CHAT', id })

  const addDocument = async (file) => {
    const chatId = stateRef.current.activeChatId
    const id = `doc_${Date.now()}`
    const objectUrl = URL.createObjectURL(file)
    dispatch({
      type: 'ADD_DOCUMENT',
      chatId,
      doc: { id, name: file.name, size: file.size, objectUrl, status: 'ingesting', pageCount: 0, chunkCount: 0 },
    })
    try {
      const result = await processDocument(file)
      dispatch({ type: 'DOCUMENT_READY', chatId, id, pageCount: result.pageCount, chunkCount: result.chunkCount, backendId: result.documentId })
    } catch {
      dispatch({ type: 'DOCUMENT_ERROR', chatId, id })
    }
  }

  const removeDocument = (id) => {
    const chatId = stateRef.current.activeChatId
    const doc = stateRef.current.chats.find((c) => c.id === chatId)?.documents.find((d) => d.id === id)
    if (doc?.objectUrl) URL.revokeObjectURL(doc.objectUrl)
    dispatch({ type: 'REMOVE_DOCUMENT', chatId, id })
  }

  const sendMessage = async (query) => {
    const chatId = stateRef.current.activeChatId
    const userMsg = { id: `msg_${Date.now()}`, role: 'user', content: query, timestamp: new Date() }
    dispatch({ type: 'ADD_USER_MESSAGE', chatId, message: userMsg })
    try {
      const docIds = stateRef.current.chats
        .find((c) => c.id === chatId)
        ?.documents.filter((d) => d.status === 'ready')
        .map((d) => d.id) ?? []
      const result = await chatQuery({ query, documentIds: docIds })
      dispatch({
        type: 'ADD_ASSISTANT_MESSAGE',
        chatId,
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
      dispatch({ type: 'GENERATION_ERROR', chatId })
    }
  }

  const activeChat = state.chats.find((c) => c.id === state.activeChatId) ?? state.chats[0]

  return (
    <ChatContext.Provider value={{
      chats: state.chats,
      activeChatId: state.activeChatId,
      documents: activeChat.documents,
      messages: activeChat.messages,
      isGenerating: activeChat.isGenerating,
      isProcessingDoc: activeChat.isProcessingDoc,
      createChat,
      selectChat,
      addDocument,
      removeDocument,
      sendMessage,
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useChat = () => {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside ChatProvider')
  return ctx
}
