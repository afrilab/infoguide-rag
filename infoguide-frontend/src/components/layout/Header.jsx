import { usePipeline, STEP_IDS } from '../../context/PipelineContext'
import { useAppMode } from '../../context/AppModeContext'
import Spinner from '../ui/Spinner'
import { cn } from '../../utils/cn'

const STEP_META = {
  ingestion:        { label: 'Ingest',     phase: 'doc' },
  preprocessing:    { label: 'Preprocess', phase: 'doc' },
  chunking:         { label: 'Chunk',      phase: 'doc' },
  embedding:        { label: 'Embed',      phase: 'doc' },
  imageDescription: { label: 'Images',     phase: 'doc' },
  queryExpansion:   { label: 'Query',      phase: 'qry' },
  retrieval:        { label: 'Retrieve',   phase: 'qry' },
  reranking:        { label: 'Rerank',     phase: 'qry' },
  generation:       { label: 'Generate',   phase: 'qry' },
}

function StepDot({ id, index, isCurrent, status, onClick }) {
  const isDone = status === 'done' || status === 'skipped'
  const isLoading = status === 'loading'
  const clickable = isDone && !isCurrent

  return (
    <button
      onClick={clickable ? onClick : undefined}
      disabled={!isDone && !isCurrent}
      className={cn('flex flex-col items-center gap-1.5', clickable ? 'cursor-pointer' : 'cursor-default')}
    >
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors',
        isCurrent && !isDone && 'bg-blue-700 text-white ring-4 ring-blue-100',
        isDone && isCurrent && 'bg-green-600 text-white ring-4 ring-green-100',
        isDone && !isCurrent && 'bg-green-600 text-white hover:bg-green-700',
        isLoading && 'bg-blue-100 text-blue-700',
        !isDone && !isCurrent && !isLoading && 'bg-slate-100 text-slate-400',
      )}>
        {isLoading ? <Spinner size="xs" /> : isDone ? (
          <svg className="w-3.5 h-3.5" viewBox="0 0 14 14" fill="none">
            <path d="M2.5 7l3 3 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        ) : String(index + 1).padStart(2, '0')}
      </div>
      <span className={cn(
        'hidden sm:block text-xs font-medium leading-none',
        isCurrent ? 'text-blue-700' : isDone ? 'text-green-700' : 'text-slate-400'
      )}>
        {STEP_META[id].label}
      </span>
    </button>
  )
}

function PhaseConnector({ done }) {
  return (
    <div className="flex-1 flex items-center pb-5">
      <div className={cn('h-px w-full transition-colors', done ? 'bg-green-300' : 'bg-slate-200')} />
    </div>
  )
}

function ModeToggle() {
  const { mode, setMode } = useAppMode()
  return (
    <div className="flex rounded-lg border border-slate-200 p-0.5 gap-0.5">
      {['chat', 'pipeline'].map((m) => (
        <button
          key={m}
          onClick={() => setMode(m)}
          className={cn(
            'px-3 py-1 text-xs font-medium rounded-md capitalize transition-colors',
            mode === m ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-700'
          )}
        >
          {m === 'pipeline' ? 'Pipeline' : 'Chat'}
        </button>
      ))}
    </div>
  )
}

export default function Header() {
  const { steps, currentStepIndex, navigateTo } = usePipeline()
  const { mode } = useAppMode()

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-slate-200">
      {/* Branding row — full width, logo anchored left */}
      <div className="px-5 flex items-center h-13 gap-3 h-12">
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-blue-700 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 16 16" fill="none">
              <circle cx="6" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="10" cy="12" r="2" stroke="currentColor" strokeWidth="1.5" />
              <path d="M6 6v2l4 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-slate-900 tracking-tight">InfoGuide</span>
          <div className="hidden sm:block w-px h-3.5 bg-slate-200" />
          <span className="hidden sm:inline text-xs text-slate-400 font-medium">RAG Pipeline</span>
        </div>

        <div className="flex-1" />

        {mode === 'pipeline' && (
          <span className="text-xs text-slate-400 font-medium tabular-nums">
            Step {currentStepIndex + 1}/{STEP_IDS.length}
          </span>
        )}

        <ModeToggle />
      </div>

      {/* Step progress row — pipeline only */}
      {mode === 'pipeline' && (
        <div className="border-t border-slate-100 py-2.5">
        <div className="max-w-4xl mx-auto px-5 flex items-center gap-1">
          {STEP_IDS.map((id, i) => {
            const isPhaseBreak = i === 5
            return (
              <div key={id} className="flex items-center gap-1 flex-1 min-w-0">
                {isPhaseBreak && <div className="w-px h-6 bg-slate-200 mx-1 shrink-0 self-start mt-1" />}
                <StepDot
                  id={id}
                  index={i}
                  isCurrent={i === currentStepIndex}
                  status={steps[id].status}
                  onClick={() => navigateTo(i)}
                />
                {i < STEP_IDS.length - 1 && i !== 4 && (
                  <PhaseConnector done={steps[id].status === 'done' || steps[id].status === 'skipped'} />
                )}
              </div>
            )
          })}
        </div>
        </div>
      )}
    </header>
  )
}
