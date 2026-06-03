import { cn } from '../../utils/cn'

export default function ChunkCard({ chunk, rank, score, highlight = false, className }) {
  return (
    <div
      className={cn(
        'border rounded-lg p-4 bg-white',
        highlight ? 'border-blue-200 bg-blue-50/30' : 'border-slate-200',
        className
      )}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          {rank != null && (
            <span className="shrink-0 w-5 h-5 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold flex items-center justify-center">
              {rank}
            </span>
          )}
          <span className="text-xs font-semibold text-slate-700 truncate">{chunk.heading}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {chunk.metadata?.type === 'image_description' && (
            <span className="px-1.5 py-0.5 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded">
              Image
            </span>
          )}
          {score != null && (
            <span className="text-xs text-slate-500 font-mono">{score.toFixed(3)}</span>
          )}
        </div>
      </div>
      <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">{chunk.text}</p>
      {chunk.metadata && (
        <div className="mt-2 flex gap-3 text-xs text-slate-400">
          {chunk.metadata.charCount && <span>{chunk.metadata.charCount} chars</span>}
          {chunk.metadata.pageNumbers?.length > 0 && (
            <span>p. {chunk.metadata.pageNumbers.join('–')}</span>
          )}
          {chunk.metadata.pageNumber && <span>p. {chunk.metadata.pageNumber}</span>}
        </div>
      )}
    </div>
  )
}
