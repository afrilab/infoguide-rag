import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { describeImages } from '../../api/index'

export default function ImageDescriptionStep() {
  const { steps, startStep, completeStep, errorStep } = usePipeline()
  const { status, data } = steps.imageDescription

  const handleRun = async () => {
    startStep('imageDescription')
    try {
      const result = await describeImages(steps.chunking.data?.chunks ?? [])
      completeStep('imageDescription', result)
    } catch (e) {
      errorStep('imageDescription', e.message)
    }
  }

  const imageChunks = data?.imageChunks ?? []

  return (
    <StepCard
      stepNum={5}
      title="Image Description"
      subtitle="Generate text descriptions for embedded images using GPT-4o Vision"
      status={status}
    >
      {status === 'idle' && (
        <div className="flex items-start justify-between gap-4">
          <div className="text-sm text-slate-500 space-y-1">
            <p>Filters out small or blank images, then sends each qualifying image to GPT-4o Vision.</p>
            <p>Generated descriptions are added as new chunks and embedded alongside the text chunks.</p>
          </div>
          <Button onClick={handleRun} className="shrink-0">
            Describe Images
          </Button>
        </div>
      )}

      {status === 'loading' && (
        <div className="space-y-2">
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <Spinner />
            Analyzing images with GPT-4o Vision…
          </div>
          <p className="text-xs text-slate-400">Filters blank images, then processes each with a custom vision prompt.</p>
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 text-center">
              <p className="text-lg font-semibold text-green-700">{data.processed}</p>
              <p className="text-xs text-slate-500">Images described</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 text-center">
              <p className="text-lg font-semibold text-slate-500">{data.skipped}</p>
              <p className="text-xs text-slate-500">Skipped (too small / blank)</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2.5 text-center">
              <p className="text-lg font-semibold text-blue-700">{data.newTotalChunks}</p>
              <p className="text-xs text-slate-500">Total chunks (incl. images)</p>
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Generated Image Descriptions</p>
            {imageChunks.map((chunk) => (
              <div key={chunk.id} className="border border-slate-200 rounded-lg p-4 bg-white">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-1.5 py-0.5 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded font-medium">
                    Image
                  </span>
                  <span className="text-xs text-slate-500 font-mono">{chunk.imageFile}</span>
                  {chunk.metadata?.pageNumber && (
                    <span className="text-xs text-slate-400">p. {chunk.metadata.pageNumber}</span>
                  )}
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">{chunk.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.imageDescription.error}</p>
      )}
    </StepCard>
  )
}
