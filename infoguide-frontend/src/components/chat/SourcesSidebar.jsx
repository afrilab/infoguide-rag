import { useRef } from 'react'
import { UploadCloud, FileText, X, Loader2, AlertCircle, ArrowDown, Plus, MessageSquare } from 'lucide-react'
import { useChat } from '../../context/ChatContext'
import { cn } from '../../utils/cn'

function ChatItem({ chat, isActive, onSelect }) {
  return (
    <button
      onClick={() => onSelect(chat.id)}
      className={cn(
        'w-full text-left px-3 py-2 rounded-lg transition-colors group',
        isActive ? 'bg-slate-700/80 text-slate-100' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
      )}
    >
      <div className="flex items-center gap-2">
        <MessageSquare className="w-3 h-3 shrink-0 opacity-50" />
        <span className="text-xs truncate leading-snug">{chat.title}</span>
      </div>
      {chat.documents.length > 0 && (
        <p className="text-xs text-slate-600 mt-0.5 pl-5 leading-none">
          {chat.documents.length} source{chat.documents.length !== 1 ? 's' : ''}
        </p>
      )}
    </button>
  )
}

function DocCard({ doc, onRemove }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 flex items-start gap-2.5">
      <FileText className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-200 truncate leading-snug">{doc.name}</p>
        {doc.status === 'ingesting' && (
          <div className="flex items-center gap-1.5 mt-1">
            <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
            <span className="text-xs text-blue-400">Processing…</span>
          </div>
        )}
        {doc.status === 'ready' && (
          <p className="text-xs text-slate-500 mt-0.5">{doc.pageCount} pages · {doc.chunkCount} chunks</p>
        )}
        {doc.status === 'error' && (
          <div className="flex items-center gap-1 mt-1">
            <AlertCircle className="w-3 h-3 text-red-400" />
            <span className="text-xs text-red-400">Processing failed</span>
          </div>
        )}
      </div>
      <button onClick={() => onRemove(doc.id)} className="text-slate-600 hover:text-slate-400 transition-colors mt-0.5 shrink-0">
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}

export default function SourcesSidebar() {
  const { chats, activeChatId, documents, addDocument, removeDocument, createChat, selectChat } = useChat()
  const inputRef = useRef(null)
  const isEmpty = documents.length === 0

  const handleFiles = (files) => Array.from(files).forEach((f) => addDocument(f))

  return (
    <div className="w-64 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">

      {/* ── CHATS panel ── */}
      <div className="flex-1 flex flex-col min-h-0 border-b border-slate-800">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 shrink-0">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Chats</h2>
          <button
            onClick={createChat}
            className="flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5 scrollbar-thin">
          {chats.map((chat) => (
            <ChatItem key={chat.id} chat={chat} isActive={chat.id === activeChatId} onSelect={selectChat} />
          ))}
        </div>
      </div>

      {/* ── SOURCES panel ── */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 shrink-0">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Sources</h2>
          <button
            onClick={() => inputRef.current?.click()}
            className="flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
          >
            <span className="text-base leading-none">+</span> Add
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.docx"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2 scrollbar-thin">
          {documents.map((doc) => (
            <DocCard key={doc.id} doc={doc} onRemove={removeDocument} />
          ))}
          {isEmpty && (
            <div
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); handleFiles(e.dataTransfer.files) }}
              className="rounded-xl border-2 border-dashed border-blue-500/50 bg-blue-900/20 hover:bg-blue-900/30 cursor-pointer transition-all duration-300 text-center p-5"
            >
              <div className="flex justify-center mb-1">
                <ArrowDown className="w-4 h-4 text-blue-400 animate-bounce" />
              </div>
              <UploadCloud className="w-6 h-6 text-blue-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-blue-300 animate-pulse">Add your first source</p>
              <p className="text-xs text-slate-500 mt-1">PDF, TXT, DOCX</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Partner logos ── */}
      <div className="px-4 py-4 border-t border-slate-800 flex items-center gap-4 shrink-0">
        <img src="/sabanci.svg" alt="Sabancı University" className="h-7 object-contain rounded opacity-90 hover:opacity-100 transition-opacity" />
        <div className="w-px h-5 bg-slate-700" />
        <img src="/akbank.svg" alt="Akbank" className="h-3.5 object-contain opacity-90 hover:opacity-100 transition-opacity" />
      </div>
    </div>
  )
}
