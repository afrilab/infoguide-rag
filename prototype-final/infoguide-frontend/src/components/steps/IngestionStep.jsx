import { useRef, useState } from 'react'
import { UploadCloud, FileText, X } from 'lucide-react'
import StepCard from '../ui/StepCard'
import Button from '../ui/Button'
import Spinner from '../ui/Spinner'
import { usePipeline } from '../../context/PipelineContext'
import { ingestDocument } from '../../api/index'
import { cn } from '../../utils/cn'

function FileDropZone({ onFile, file }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  if (file) {
    return (
      <div className="flex items-center justify-between p-4 border border-green-200 bg-green-50 rounded-lg">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-green-600" />
          <div>
            <p className="text-sm font-medium text-slate-900">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        </div>
        <button onClick={() => onFile(null)} className="text-slate-400 hover:text-slate-600">
          <X className="w-4 h-4" />
        </button>
      </div>
    )
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors',
        dragging ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.docx"
        className="hidden"
        onChange={(e) => onFile(e.target.files[0] ?? null)}
      />
      <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-3" />
      <p className="text-sm font-medium text-slate-700">Drop a file here or click to browse</p>
      <p className="text-xs text-slate-400 mt-1">PDF, TXT, DOCX</p>
    </div>
  )
}

export default function IngestionStep() {
  const { steps, startStep, completeStep, errorStep } = usePipeline()
  const { status, data } = steps.ingestion
  const [file, setFile] = useState(null)

  const handleRun = async () => {
    if (!file) return
    startStep('ingestion')
    try {
      const result = await ingestDocument(file)
      completeStep('ingestion', result)
    } catch (e) {
      errorStep('ingestion', e.message)
    }
  }

  return (
    <StepCard
      stepNum={1}
      title="Document Ingestion"
      subtitle="Upload a document to extract text, tables, and images"
      status={status}
    >
      {status === 'idle' && (
        <div className="space-y-4">
          <FileDropZone onFile={setFile} file={file} />
          <div className="flex justify-end">
            <Button onClick={handleRun} disabled={!file}>
              Extract Content
            </Button>
          </div>
        </div>
      )}

      {status === 'loading' && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <Spinner />
          Extracting text, tables, and images…
        </div>
      )}

      {status === 'done' && data && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Pages', value: data.pages },
              { label: 'Images found', value: data.extractedImages },
              { label: 'Tables found', value: data.extractedTables },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 rounded-lg p-3 text-center">
                <p className="text-xl font-semibold text-slate-900">{value}</p>
                <p className="text-xs text-slate-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Extracted Text Preview</p>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 max-h-52 overflow-y-auto scrollbar-thin">
              <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                {data.rawText?.slice(0, 800)}{data.rawText?.length > 800 ? '\n\n[…]' : ''}
              </pre>
            </div>
          </div>
        </div>
      )}

      {status === 'error' && (
        <p className="text-sm text-red-600">Error: {steps.ingestion.error}</p>
      )}
    </StepCard>
  )
}
