import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { preprocessText } from '../../api/index'

export default function PreprocessingStep() {
  const { steps, startStep, completeStep, errorStep } = usePipeline()
  const { status, data } = steps.preprocessing
  const ingestionData = steps.ingestion.data

  const handleRun = async () => {
    startStep('preprocessing')
    try {
      const result = await preprocessText(ingestionData?.rawText ?? '')
      completeStep('preprocessing', result)
    } catch (e) {
      errorStep('preprocessing', e.message)
    }
  }

  const stats = data?.stats ?? {}

  return (
    <StepCard
      stepNum={2}
      title="Text Preprocessing"
      subtitle="Clean and normalize extracted text"
      status={status}
    >
      {status === 'idle' && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Removes invisible characters, fixes hyphenation, deduplicates headers and footers.
          </p>
          <Button onClick={handleRun} className="shrink-0 ml-4">
            Run Preprocessing
          </Button>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Cleaning and normalizing text…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              { label: 'Invisible chars removed', value: stats.removedInvisibleChars },
              { label: 'Hyphenations fixed', value: stats.fixedHyphenations },
              { label: 'Repeated headers removed', value: stats.removedHeaders },
              { label: 'Repeated footers removed', value: stats.removedFooters },
              { label: 'Extra spaces normalized', value: stats.normalizedSpaces },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 rounded-lg p-3">
                <p className="text-lg font-semibold text-slate-900">{value ?? '—'}</p>
                <p className="text-xs text-slate-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Before</p>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 max-h-44 overflow-y-auto scrollbar-thin">
                <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans leading-relaxed">
                  {ingestionData?.rawText?.slice(0, 500) ?? ''}{(ingestionData?.rawText?.length ?? 0) > 500 ? '\n[…]' : ''}
                </pre>
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-green-600 uppercase tracking-wide mb-2">After</p>
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 max-h-44 overflow-y-auto scrollbar-thin">
                <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {data.cleanedText?.slice(0, 500) ?? ''}{(data.cleanedText?.length ?? 0) > 500 ? '\n[…]' : ''}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.preprocessing.error}</p>
      )}
    </StepCard>
  )
}
