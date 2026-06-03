import { AppModeProvider, useAppMode } from './context/AppModeContext'
import { PipelineProvider, STEP_IDS, usePipeline } from './context/PipelineContext'
import { ChatProvider } from './context/ChatContext'
import Header from './components/layout/Header'
import Button from './components/ui/Button'
import ChatView from './components/chat/ChatView'
import IngestionStep from './components/steps/IngestionStep'
import PreprocessingStep from './components/steps/PreprocessingStep'
import ChunkingStep from './components/steps/ChunkingStep'
import EmbeddingStep from './components/steps/EmbeddingStep'
import ImageDescriptionStep from './components/steps/ImageDescriptionStep'
import QueryExpansionStep from './components/steps/QueryExpansionStep'
import RetrievalStep from './components/steps/RetrievalStep'
import RerankingStep from './components/steps/RerankingStep'
import GenerationStep from './components/steps/GenerationStep'
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react'

const STEP_COMPONENTS = {
  ingestion: IngestionStep,
  preprocessing: PreprocessingStep,
  chunking: ChunkingStep,
  embedding: EmbeddingStep,
  imageDescription: ImageDescriptionStep,
  queryExpansion: QueryExpansionStep,
  retrieval: RetrievalStep,
  reranking: RerankingStep,
  generation: GenerationStep,
}

const PHASE_LABELS = {
  ingestion: 'Document Processing',
  preprocessing: 'Document Processing',
  chunking: 'Document Processing',
  embedding: 'Document Processing',
  imageDescription: 'Document Processing',
  queryExpansion: 'Query Pipeline',
  retrieval: 'Query Pipeline',
  reranking: 'Query Pipeline',
  generation: 'Query Pipeline',
}

function PipelineWizard() {
  const { steps, currentStepIndex, goNext, goPrev } = usePipeline()

  const currentId = STEP_IDS[currentStepIndex]
  const CurrentStep = STEP_COMPONENTS[currentId]
  const currentStatus = steps[currentId].status
  const isDone = currentStatus === 'done' || currentStatus === 'skipped'
  const isFirstStep = currentStepIndex === 0
  const isLastStep = currentStepIndex === STEP_IDS.length - 1

  return (
    <>
      <Header />
      <main className="flex-1 overflow-y-auto max-w-3xl mx-auto w-full px-4 py-4 flex flex-col gap-3">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          {PHASE_LABELS[currentId]}
        </p>

        <CurrentStep key={currentId} />

        <div className="flex items-center justify-between">
          <Button variant="secondary" onClick={goPrev} disabled={isFirstStep} className="gap-2">
            <ArrowLeft className="w-4 h-4" /> Back
          </Button>

          {isDone && isLastStep ? (
            <div className="flex items-center gap-2 text-sm font-medium text-green-700">
              <CheckCircle2 className="w-5 h-5" />
              Pipeline complete
            </div>
          ) : isDone ? (
            <Button onClick={goNext} className="gap-2">
              Continue <ArrowRight className="w-4 h-4" />
            </Button>
          ) : (
            <div />
          )}
        </div>
      </main>
    </>
  )
}

function AppRouter() {
  const { mode } = useAppMode()
  return (
    <div className="h-screen overflow-hidden bg-slate-50 flex flex-col">
      {mode === 'pipeline' ? <PipelineWizard /> : <ChatView />}
    </div>
  )
}

export default function App() {
  return (
    <AppModeProvider>
      <PipelineProvider>
        <ChatProvider>
          <AppRouter />
        </ChatProvider>
      </PipelineProvider>
    </AppModeProvider>
  )
}
