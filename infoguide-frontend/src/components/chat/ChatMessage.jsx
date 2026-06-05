import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react'
import PipelineDetails from './PipelineDetails'
import { useChat } from '../../context/ChatContext'
import { cn } from '../../utils/cn'

function MarkdownAnswer({ text }) {
  return (
    <div className="text-sm text-slate-800 leading-relaxed space-y-2">
      {text.split('\n').map((line, i) => {
        if (/^\*\*\d+\./.test(line)) {
          return <p key={i} className="font-semibold mt-2">{line.replace(/\*\*/g, '')}</p>
        }
        if (line.startsWith('**') && line.endsWith('**')) {
          return <p key={i} className="font-semibold">{line.slice(2, -2)}</p>
        }
        if (line.trim() === '') return <div key={i} className="h-1" />
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

function SourcesSection({ sources }) {
  const [open, setOpen] = useState(false)
  const { documents } = useChat()
  if (!sources?.length) return null

  return (
    <div className="border-t border-slate-100 pt-2 mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {sources.length} source{sources.length !== 1 ? 's' : ''} used
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {sources.map((src, i) => {
            const doc = documents.find((d) => d.backendId === src.documentId)
              ?? documents.find((d) => d.status === 'ready' && d.objectUrl)
            const canView = doc?.objectUrl && src.pageNumber
            return (
              <div key={src.chunkId ?? i} className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2">
                <div className="flex items-start justify-between gap-2 mb-0.5">
                  <p className="text-xs font-semibold text-slate-700">{src.heading}</p>
                  {canView && (
                    <a
                      href={`${doc.objectUrl}#page=${src.pageNumber}`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-blue-500 transition-colors shrink-0"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Go to document · p.{src.pageNumber}
                    </a>
                  )}
                </div>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{src.text}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function MessageActions({ content }) {
  const [copied, setCopied] = useState(false)
  const [vote, setVote] = useState(null)

  const copy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-1 mt-3 pt-2 border-t border-slate-100">
      <button
        onClick={() => setVote(vote === 'up' ? null : 'up')}
        className={cn(
          'p-1.5 rounded-md transition-colors',
          vote === 'up' ? 'text-blue-600 bg-blue-50' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
        )}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => setVote(vote === 'down' ? null : 'down')}
        className={cn(
          'p-1.5 rounded-md transition-colors',
          vote === 'down' ? 'text-red-500 bg-red-50' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
        )}
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
      <div className="w-px h-3.5 bg-slate-200 mx-0.5" />
      <button
        onClick={copy}
        className={cn(
          'flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs transition-colors',
          copied ? 'text-green-600 bg-green-50' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
        )}
      >
        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  )
}

export default function ChatMessage({ message }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-lg bg-blue-700 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-2xl w-full">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-6 h-6 rounded-full bg-blue-700 flex items-center justify-center shrink-0">
            <svg className="w-3 h-3 text-white" viewBox="0 0 16 16" fill="none">
              <circle cx="6" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="10" cy="12" r="2" stroke="currentColor" strokeWidth="1.5" />
              <path d="M6 6v2l4 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className="text-xs font-medium text-slate-500">InfoGuide</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
          <MarkdownAnswer text={message.content} />
          {message.sources && <SourcesSection sources={message.sources} />}
          {message.pipelineDetails && <PipelineDetails details={message.pipelineDetails} />}
          <MessageActions content={message.content} />
        </div>
      </div>
    </div>
  )
}
