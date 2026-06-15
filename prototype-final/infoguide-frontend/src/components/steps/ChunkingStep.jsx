import { useState } from 'react'
import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import ChunkCard from '../ui/ChunkCard'
import { usePipeline } from '../../context/PipelineContext'
import { chunkText } from '../../api/index'

export default function ChunkingStep() {
  const { steps, startStep, completeStep, errorStep } = usePipeline()
  const { status, data } = steps.chunking
  const [showAll, setShowAll] = useState(false)

  const handleRun = async () => {
    startStep('chunking')
    try {
      const result = await chunkText(steps.preprocessing.data?.cleanedText ?? '')
      completeStep('chunking', result)
    } catch (e) {
      errorStep('chunking', e.message)
    }
  }

  const chunks = data?.chunks ?? []
  const visible = showAll ? chunks : chunks.slice(0, 4)

  return (
    <StepCard
      stepNum={3}
      title="Text Chunking"
      subtitle="Split document into overlapping, heading-aware chunks"
      status={status}
    >
      {status === 'idle' && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Heading-aware recursive chunking with overlap. Max 1,800 chars, 250-char overlap.
          </p>
          <Button onClick={handleRun} className="shrink-0 ml-4">
            Run Chunking
          </Button>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Splitting document into chunks…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-slate-900">{data.totalChunks}</span> chunks created
            </p>
          </div>
          <div className="space-y-3">
            {visible.map((chunk) => (
              <ChunkCard key={chunk.id} chunk={chunk} />
            ))}
          </div>
          {chunks.length > 4 && (
            <button
              onClick={() => setShowAll((s) => !s)}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              {showAll ? 'Show less' : `Show all ${chunks.length} chunks`}
            </button>
          )}
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.chunking.error}</p>
      )}
    </StepCard>
  )
}
