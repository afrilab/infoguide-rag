import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { retrieveChunks } from '../../api/index'
import { cn } from '../../utils/cn'

const METHODS = [
  { id: 'faiss', label: 'FAISS', desc: 'Dense semantic retrieval' },
  { id: 'bm25', label: 'BM25', desc: 'Lexical keyword matching' },
  { id: 'hybrid', label: 'Hybrid', desc: 'RRF fusion of both' },
]

export default function RetrievalStep() {
  const {
    steps, startStep, completeStep, errorStep,
    retrievalMethod, topK, dispatch, query,
  } = usePipeline()
  const { status, data } = steps.retrieval

  const expandedQuery = steps.queryExpansion.data?.expandedQuery ?? query
  const subQueries = steps.queryDecomposition.data?.subQueries ?? null

  const handleRun = async () => {
    startStep('retrieval')
    try {
      const result = await retrieveChunks({ query, expandedQuery, subQueries, method: retrievalMethod, topK })
      completeStep('retrieval', result)
    } catch (e) {
      errorStep('retrieval', e.message)
    }
  }

  const isHybrid = (data?.method ?? retrievalMethod) === 'hybrid'
  const results = data?.results ?? []

  return (
    <StepCard
      stepNum={8}
      title="Retrieval"
      subtitle="Find the most relevant chunks for the query"
      status={status}
    >
      {status === 'idle' && (
        <div className="space-y-5">
          <div>
            <p className="text-xs font-medium text-slate-600 mb-2">Retrieval Method</p>
            <div className="flex gap-2">
              {METHODS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => dispatch({ type: 'SET_RETRIEVAL_METHOD', method: m.id })}
                  className={cn(
                    'flex-1 border rounded-lg p-3 text-left transition-colors',
                    retrievalMethod === m.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  )}
                >
                  <p className={cn('text-sm font-semibold', retrievalMethod === m.id ? 'text-blue-700' : 'text-slate-700')}>
                    {m.label}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{m.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-slate-600">Top-K Results</p>
              <span className="text-sm font-semibold text-slate-900">{topK}</span>
            </div>
            <input
              type="range"
              min={1} max={20} value={topK}
              onChange={(e) => dispatch({ type: 'SET_TOP_K', topK: Number(e.target.value) })}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>1</span><span>20</span>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleRun}>Run Retrieval</Button>
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Searching index with {retrievalMethod.toUpperCase()} method…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-500">Method:</span>
            <span className="font-semibold text-slate-800 capitalize">{data.method}</span>
            <span className="text-slate-300">·</span>
            <span className="text-slate-500">Top-K:</span>
            <span className="font-semibold text-slate-800">{data.topK}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">Rank</th>
                  <th className="text-left py-2 pr-4 text-xs font-medium text-slate-500">Section</th>
                  {isHybrid && <th className="text-center py-2 pr-4 text-xs font-medium text-slate-500">FAISS</th>}
                  {isHybrid && <th className="text-center py-2 pr-4 text-xs font-medium text-slate-500">BM25</th>}
                  <th className="text-right py-2 text-xs font-medium text-slate-500">Score</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.chunkId} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2.5 pr-4">
                      <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold inline-flex items-center justify-center">
                        {r.rank}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <p className="font-medium text-slate-800 text-sm">{r.heading}</p>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{r.text}</p>
                    </td>
                    {isHybrid && <td className="py-2.5 pr-4 text-center text-xs text-slate-500">{r.faissRank}</td>}
                    {isHybrid && <td className="py-2.5 pr-4 text-center text-xs text-slate-500">{r.bm25Rank}</td>}
                    <td className="py-2.5 text-right font-mono text-xs text-slate-700">{r.score.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.retrieval.error}</p>
      )}
    </StepCard>
  )
}
