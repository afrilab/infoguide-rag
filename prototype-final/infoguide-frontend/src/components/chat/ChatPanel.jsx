import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import ChatMessage from './ChatMessage'
import Spinner from '../ui/Spinner'
import { useChat } from '../../context/ChatContext'
import { cn } from '../../utils/cn'

function EmptyState() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
      <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-blue-600" viewBox="0 0 24 24" fill="none">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">Ask anything about your sources</h3>
      <p className="text-sm text-slate-400 max-w-sm">
        Your answers will be grounded in the documents you've added. Add at least one source to get started.
      </p>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <Spinner size="xs" />
        <span className="text-xs text-slate-500">Searching your sources…</span>
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const { messages, isGenerating, documents, sendMessage } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const hasReadyDocs = documents.some((d) => d.status === 'ready')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isGenerating])

  const handleSend = () => {
    const q = input.trim()
    if (!q || isGenerating || !hasReadyDocs) return
    setInput('')
    sendMessage(q)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const canSend = input.trim().length > 0 && !isGenerating && hasReadyDocs

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 scrollbar-thin">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isGenerating && <ThinkingIndicator />}
            <div ref={bottomRef} />
          </>
        )}
        {messages.length === 0 && <div ref={bottomRef} />}
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        {!hasReadyDocs && documents.length > 0 && (
          <p className="text-xs text-amber-600 mb-2 text-center">
            Processing your document… you can type while you wait.
          </p>
        )}
        {!hasReadyDocs && documents.length === 0 && (
          <p className="text-xs text-slate-400 mb-2 text-center">
            Add a source on the left to start chatting.
          </p>
        )}
        <div className={cn(
          'flex items-end gap-2 border rounded-xl px-3 py-2 transition-colors',
          canSend ? 'border-blue-300 bg-white' : 'border-slate-200 bg-slate-50'
        )}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
            onKeyDown={handleKeyDown}
            placeholder={hasReadyDocs ? 'Ask a question about your documents…' : 'Add a source first…'}
            disabled={!hasReadyDocs && documents.length === 0}
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none disabled:cursor-not-allowed"
            style={{ minHeight: '24px', maxHeight: '120px' }}
          />
          <button
            onClick={handleSend}
            disabled={!canSend}
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center transition-colors shrink-0',
              canSend
                ? 'bg-blue-700 hover:bg-blue-800 text-white'
                : 'bg-slate-100 text-slate-300 cursor-not-allowed'
            )}
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-xs text-slate-300 mt-1.5 text-right">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  )
}
