import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { generateEmbeddings } from '../../api/index'

export default function EmbeddingStep() {
  const { steps, startStep, completeStep, errorStep } = usePipeline()
  const { status, data } = steps.embedding

  const handleRun = async () => {
    startStep('embedding')
    try {
      const result = await generateEmbeddings(steps.chunking.data?.chunks ?? [])
      completeStep('embedding', result)
    } catch (e) {
      errorStep('embedding', e.message)
    }
  }

  return (
    <StepCard
      stepNum={4}
      title="Embedding Generation"
      subtitle="Encode chunks into dense vector representations"
      status={status}
    >
      {status === 'idle' && (
        <div className="flex items-start justify-between gap-4">
          <div className="text-sm text-slate-500 space-y-1">
            <p>Uses <span className="font-mono text-xs bg-slate-100 px-1 py-0.5 rounded">BAAI/bge-m3</span> — a multilingual model supporting dense retrieval.</p>
            <p>Vectors are L2-normalized and saved to an index for fast retrieval.</p>
          </div>
          <Button onClick={handleRun} className="shrink-0">
            Generate Embeddings
          </Button>
        </div>
      )}

      {status === 'loading' && (
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <Spinner />
            Encoding {steps.chunking.data?.totalChunks ?? '…'} chunks with bge-m3…
          </div>
          <p className="text-xs text-slate-400">This may take 10–40 seconds depending on document size.</p>
        </div>
      )}

      {status === 'done' && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Model', value: data.model },
            { label: 'Vector dimension', value: data.dimension.toLocaleString() },
            { label: 'Chunks embedded', value: data.totalChunks },
            { label: 'Processing time', value: `${data.processingTimeSeconds}s` },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <p className="text-sm font-semibold text-slate-900 truncate">{value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.embedding.error}</p>
      )}
    </StepCard>
  )
}
