import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import ChunkCard from '../ui/ChunkCard'
import { usePipeline } from '../../context/PipelineContext'
import { generateAnswer } from '../../api/index'

function MarkdownAnswer({ text }) {
  const lines = text.split('\n')
  return (
    <div className="text-base text-slate-800 leading-relaxed space-y-2">
      {lines.map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <p key={i} className="font-semibold">{line.slice(2, -2)}</p>
        }
        if (/^\*\*\d+\./.test(line)) {
          const cleaned = line.replace(/\*\*/g, '')
          return <p key={i} className="font-semibold mt-3">{cleaned}</p>
        }
        if (line.trim() === '') return <div key={i} className="h-1" />
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

export default function GenerationStep() {
  const { steps, startStep, completeStep, errorStep, query } = usePipeline()
  const { status, data } = steps.generation

  const rerankData = steps.reranking.data
  const contextChunks = rerankData?.results ?? steps.retrieval.data?.results ?? []

  const getChunkById = (id) => {
    const allChunks = [
      ...(steps.chunking.data?.chunks ?? []),
      ...(steps.imageDescription.data?.imageChunks ?? []),
    ]
    return allChunks.find((c) => c.id === id)
  }

  const handleRun = async () => {
    startStep('generation')
    try {
      const result = await generateAnswer({ query, chunks: contextChunks })
      completeStep('generation', result)
    } catch (e) {
      errorStep('generation', e.message)
    }
  }

  return (
    <StepCard
      stepNum={10}
      title="Answer Generation"
      subtitle="Generate a grounded answer using only the retrieved context"
      status={status}
    >
      {status === 'idle' && (
        <div className="space-y-4">
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Query</p>
            <p className="text-sm text-slate-800 font-medium">{query}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
              Context Chunks ({contextChunks.length})
            </p>
            <div className="space-y-2">
              {contextChunks.slice(0, 3).map((r, i) => (
                <div key={r.chunkId ?? i} className="flex items-center gap-3 text-sm text-slate-600 py-1.5 border-b border-slate-100">
                  <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold flex items-center justify-center shrink-0">
                    {r.newRank ?? r.rank ?? i + 1}
                  </span>
                  <span className="font-medium text-slate-700 truncate">{r.heading}</span>
                </div>
              ))}
              {contextChunks.length > 3 && (
                <p className="text-xs text-slate-400">+{contextChunks.length - 3} more chunks</p>
              )}
            </div>
          </div>
          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-slate-500">
              Model: <span className="font-mono">gpt-4o-mini</span> · Strict RAG prompt
            </p>
            <Button onClick={handleRun}>Generate Answer</Button>
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Generating answer with GPT-4o mini…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-6">
          <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 flex items-start gap-3">
            <svg className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M3 13c0-2.761 2.239-5 5-5s5 2.239 5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <p className="text-sm text-slate-700 italic">"{query}"</p>
          </div>

          <div className="rounded-xl border border-blue-100 bg-gradient-to-b from-blue-50/60 to-white shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-blue-100 bg-blue-50/80">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-sm font-semibold text-slate-800">Answer</span>
              </div>
              <div className="flex gap-3 text-xs text-slate-400">
                <span className="font-mono">{data.model}</span>
                <span>·</span>
                <span>{data.inputTokens?.toLocaleString()} in / {data.outputTokens?.toLocaleString()} out</span>
              </div>
            </div>
            <div className="px-6 py-5">
              <MarkdownAnswer text={data.answer} />
            </div>
          </div>

          {data.citedChunks?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">
                Supporting Evidence — {data.citedChunks.length} source chunks
              </p>
              <div className="space-y-2">
                {data.citedChunks.map((cite, i) => {
                  const chunk = getChunkById(cite.chunkId)
                  return chunk ? (
                    <ChunkCard key={cite.chunkId} chunk={chunk} rank={i + 1} highlight />
                  ) : (
                    <div key={cite.chunkId} className="border border-slate-200 rounded-lg p-3 text-sm text-slate-600">
                      {cite.heading}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.generation.error}</p>
      )}
    </StepCard>
  )
}
