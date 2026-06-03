import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '../../utils/cn'

const METHOD_LABELS = {
  hybrid: 'Hybrid (BM25 + FAISS)',
  faiss: 'Semantic (FAISS)',
  bm25: 'Keyword (BM25)',
}

const METHOD_DEFINITIONS = {
  hybrid: 'Combines keyword matching and semantic understanding, then merges the two ranked lists. Usually the most reliable method.',
  faiss: 'Finds chunks whose meaning is closest to your question, even if they use different words.',
  bm25: 'Finds chunks containing the exact keywords from your question. Fast and precise for specific terms.',
}

function Row({ label, value, definition }) {
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">{label}</span>
        <span className="text-xs font-medium text-slate-800">{value}</span>
      </div>
      {definition && (
        <p className="text-xs text-slate-400 leading-relaxed pl-0">{definition}</p>
      )}
    </div>
  )
}

export default function PipelineDetails({ details }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border-t border-slate-100 pt-2 mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        How this answer was found
      </button>

      {open && (
        <div className="mt-3 space-y-3 pl-1">
          <Row
            label="Search method:"
            value={METHOD_LABELS[details.method] ?? details.method}
            definition={METHOD_DEFINITIONS[details.method]}
          />

          <Row
            label="Retrieved:"
            value={`${details.retrieved} chunks → top ${details.reranked} after reranking`}
            definition="Reranking is a second-pass step that re-scores retrieved results using a more precise cross-encoder model, keeping only the most relevant ones."
          />

          <div className="flex items-center gap-2 pt-0.5">
            <span className="text-xs text-slate-400 font-mono">{details.model}</span>
            <span className="text-xs text-slate-300">·</span>
            <span className="text-xs text-slate-400 font-mono">
              {details.inputTokens?.toLocaleString()} in / {details.outputTokens} out
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
