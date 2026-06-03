import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { rerankChunks } from '../../api/index'
import { cn } from '../../utils/cn'

export default function RerankingStep() {
  const {
    steps, startStep, completeStep, errorStep, skipStep,
    rerankingEnabled, topKRerank, dispatch, query,
  } = usePipeline()
  const { status, data } = steps.reranking

  const retrievalChunks = steps.retrieval.data?.results ?? []

  const handleRun = async () => {
    startStep('reranking')
    try {
      const result = await rerankChunks({ query, chunks: retrievalChunks, topK: topKRerank })
      completeStep('reranking', result)
    } catch (e) {
      errorStep('reranking', e.message)
    }
  }

  const handleSkip = () => {
    skipStep('reranking', { results: retrievalChunks.slice(0, topKRerank) })
  }

  const results = data?.results ?? []

  const rankDelta = (r) => r.originalRank - r.newRank
  const deltaLabel = (d) => {
    if (d > 0) return <span className="text-green-600">+{d} ↑</span>
    if (d < 0) return <span className="text-red-500">{d} ↓</span>
    return <span className="text-slate-400">—</span>
  }

  return (
    <StepCard
      stepNum={8}
      title="Reranking"
      subtitle="Cross-encoder reranker re-scores and re-orders retrieved chunks"
      status={status}
    >
      {status === 'idle' && (
        <div className="space-y-5">
          <div className="flex items-center gap-3 p-4 border border-slate-200 rounded-lg bg-slate-50">
            <label className="flex items-center gap-3 cursor-pointer flex-1">
              <div
                onClick={() => dispatch({ type: 'TOGGLE_RERANKING' })}
                className={cn(
                  'relative w-10 h-5 rounded-full transition-colors',
                  rerankingEnabled ? 'bg-blue-600' : 'bg-slate-300'
                )}
              >
                <div className={cn(
                  'absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform',
                  rerankingEnabled ? 'translate-x-5' : 'translate-x-0.5'
                )} />
              </div>
              <span className="text-sm font-medium text-slate-700">Enable Reranking</span>
            </label>
            <div className="text-xs text-slate-500 text-right">
              Model: <span className="font-mono">BAAI/bge-reranker-v2-m3</span>
            </div>
          </div>

          {rerankingEnabled && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-600">Top-K after reranking</p>
                <span className="text-sm font-semibold text-slate-900">{topKRerank}</span>
              </div>
              <input
                type="range"
                min={1} max={steps.retrieval.data?.topK ?? 10} value={topKRerank}
                onChange={(e) => dispatch({ type: 'SET_TOP_K_RERANK', topK: Number(e.target.value) })}
                className="w-full accent-blue-600"
              />
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <Button variant="secondary" onClick={handleSkip}>Skip Reranking</Button>
            {rerankingEnabled && <Button onClick={handleRun}>Run Reranking</Button>}
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Reranking {retrievalChunks.length} chunks with cross-encoder…
        </div>
      )}

      {(status === 'done' || status === 'skipped') && data && (
        <div className="space-y-4">
          {status === 'skipped' ? (
            <p className="text-sm text-slate-500 italic">Reranking was skipped. Using retrieval order.</p>
          ) : (
            <>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{results.length}</span> chunks selected after reranking
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">New</th>
                      <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">Was</th>
                      <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">Δ</th>
                      <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">Section</th>
                      <th className="text-right py-2 text-xs font-medium text-slate-500">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r) => (
                      <tr key={r.chunkId} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2.5 pr-4">
                          <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold inline-flex items-center justify-center">
                            {r.newRank}
                          </span>
                        </td>
                        <td className="py-2.5 pr-4 text-xs text-slate-500">{r.originalRank}</td>
                        <td className="py-2.5 pr-4 text-xs font-medium">{deltaLabel(rankDelta(r))}</td>
                        <td className="py-2.5 pr-4">
                          <p className="font-medium text-slate-800">{r.heading}</p>
                          <p className="text-xs text-slate-400 line-clamp-1">{r.text}</p>
                        </td>
                        <td className="py-2.5 text-right font-mono text-xs text-slate-700">
                          {r.rerankScore.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.reranking.error}</p>
      )}
    </StepCard>
  )
}
