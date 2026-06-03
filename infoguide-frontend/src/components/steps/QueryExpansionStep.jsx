import { useState } from 'react'
import { Search } from 'lucide-react'
import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { expandQuery } from '../../api/index'

export default function QueryExpansionStep() {
  const { steps, startStep, completeStep, errorStep, query, dispatch } = usePipeline()
  const { status, data } = steps.queryExpansion
  const [localQuery, setLocalQuery] = useState(query || '')

  const handleRun = async () => {
    const q = localQuery.trim()
    if (!q) return
    dispatch({ type: 'SET_QUERY', query: q })
    startStep('queryExpansion')
    try {
      const result = await expandQuery(q)
      completeStep('queryExpansion', result)
    } catch (e) {
      errorStep('queryExpansion', e.message)
    }
  }

  return (
    <StepCard
      stepNum={6}
      title="Query Input & Expansion"
      subtitle="Enter your question and let GPT-4o mini enrich it for better retrieval"
      status={status}
    >
      {(status === 'idle' || status === 'error') && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">Your Question</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRun()}
                placeholder="What were the main drivers of revenue growth in Q3?"
                className="w-full pl-9 pr-4 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          {status === 'error' && (
            <p className="text-sm text-red-600">{steps.queryExpansion.error}</p>
          )}
          <div className="flex justify-end">
            <Button onClick={handleRun} disabled={!localQuery.trim()}>
              Expand Query
            </Button>
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <Spinner />
            Expanding query with GPT-4o mini…
          </div>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <p className="text-xs text-slate-500 mb-1">Original query</p>
            <p className="text-sm text-slate-700">{query}</p>
          </div>
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Original Query</p>
              <p className="text-sm text-slate-800">{query}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Detected Intent</p>
              <p className="text-sm text-slate-700">{data.intent}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {data.keywords?.map((kw) => (
                  <span key={kw} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-xs font-medium text-blue-600 uppercase tracking-wide mb-1">Expanded Query</p>
              <p className="text-sm text-slate-800 font-medium leading-relaxed">{data.expandedQuery}</p>
            </div>
          </div>
        </div>
      )}
    </StepCard>
  )
}
