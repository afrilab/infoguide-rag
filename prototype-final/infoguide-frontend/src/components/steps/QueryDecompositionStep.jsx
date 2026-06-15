import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { decomposeQuery } from '../../api/index'

export default function QueryDecompositionStep() {
  const { steps, startStep, completeStep, errorStep, query } = usePipeline()
  const { status, data } = steps.queryDecomposition

  const expandedQuery = steps.queryExpansion.data?.expandedQuery ?? query

  const handleRun = async () => {
    startStep('queryDecomposition')
    try {
      const result = await decomposeQuery(expandedQuery)
      completeStep('queryDecomposition', result)
    } catch (e) {
      errorStep('queryDecomposition', e.message)
    }
  }

  const subQueries = data?.subQueries ?? []

  return (
    <StepCard
      stepNum={7}
      title="Query Decomposition"
      subtitle="Break complex queries into focused sub-queries for better retrieval"
      status={status}
    >
      {status === 'idle' && (
        <div className="space-y-4">
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
              Query to decompose
            </p>
            <p className="text-sm text-slate-800 leading-relaxed">{expandedQuery}</p>
          </div>
          <p className="text-sm text-slate-500">
            If the query covers multiple distinct concepts, GPT-4o mini splits it into 2–4 atomic sub-queries. Single-concept queries are returned as-is.
          </p>
          <div className="flex justify-end">
            <Button onClick={handleRun}>Decompose Query</Button>
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Decomposing query with GPT-4o mini…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Sub-queries generated:</span>
            <span className="font-semibold text-slate-800">{subQueries.length}</span>
            {subQueries.length === 1 && (
              <span className="text-xs text-slate-400 ml-1">(single concept — no decomposition needed)</span>
            )}
          </div>

          <div className="space-y-2">
            {subQueries.map((q, i) => (
              <div
                key={i}
                className="flex items-start gap-3 border border-slate-200 rounded-lg p-3 bg-slate-50"
              >
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold inline-flex items-center justify-center shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className="text-sm text-slate-800 leading-relaxed">{q}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.queryDecomposition.error}</p>
      )}
    </StepCard>
  )
}
