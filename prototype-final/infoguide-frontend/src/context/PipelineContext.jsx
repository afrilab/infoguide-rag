import { createContext, useContext, useReducer } from 'react'

export const STEP_IDS = [
  'ingestion',
  'preprocessing',
  'chunking',
  'embedding',
  'imageDescription',
  'queryExpansion',
  'queryDecomposition',
  'retrieval',
  'reranking',
  'generation',
]

const initialSteps = Object.fromEntries(
  STEP_IDS.map((id) => [id, { status: 'idle', data: null, error: null }])
)

const initialState = {
  steps: initialSteps,
  currentStepIndex: 0,
  query: '',
  rerankingEnabled: true,
  retrievalMethod: 'hybrid',
  topK: 5,
  topKRerank: 3,
}

function reducer(state, action) {
  switch (action.type) {
    case 'STEP_LOADING':
      return {
        ...state,
        steps: {
          ...state.steps,
          [action.stepId]: { status: 'loading', data: null, error: null },
        },
      }
    case 'STEP_DONE':
      return {
        ...state,
        steps: {
          ...state.steps,
          [action.stepId]: { status: 'done', data: action.data, error: null },
        },
      }
    case 'STEP_ERROR':
      return {
        ...state,
        steps: {
          ...state.steps,
          [action.stepId]: { status: 'error', data: null, error: action.error },
        },
      }
    case 'STEP_SKIPPED':
      return {
        ...state,
        steps: {
          ...state.steps,
          [action.stepId]: { status: 'skipped', data: action.data ?? null, error: null },
        },
      }
    case 'NAVIGATE_TO':
      return {
        ...state,
        currentStepIndex: Math.max(0, Math.min(action.index, STEP_IDS.length - 1)),
      }
    case 'SET_QUERY':
      return { ...state, query: action.query }
    case 'SET_RETRIEVAL_METHOD':
      return { ...state, retrievalMethod: action.method }
    case 'SET_TOP_K':
      return { ...state, topK: action.topK }
    case 'SET_TOP_K_RERANK':
      return { ...state, topKRerank: action.topK }
    case 'TOGGLE_RERANKING':
      return { ...state, rerankingEnabled: !state.rerankingEnabled }
    case 'RESET':
      return { ...initialState }
    default:
      return state
  }
}

const PipelineContext = createContext(null)

export function PipelineProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const isStepUnlocked = (stepId) => {
    const idx = STEP_IDS.indexOf(stepId)
    if (idx === 0) return true
    for (let i = 0; i < idx; i++) {
      const prev = state.steps[STEP_IDS[i]]
      if (prev.status !== 'done' && prev.status !== 'skipped') return false
    }
    return true
  }

  const isStepActive = (stepId) => {
    const s = state.steps[stepId]
    return isStepUnlocked(stepId) && s.status !== 'done' && s.status !== 'skipped'
  }

  const startStep = (stepId) => dispatch({ type: 'STEP_LOADING', stepId })
  const completeStep = (stepId, data) => dispatch({ type: 'STEP_DONE', stepId, data })
  const errorStep = (stepId, error) => dispatch({ type: 'STEP_ERROR', stepId, error })
  const skipStep = (stepId, data) => dispatch({ type: 'STEP_SKIPPED', stepId, data })

  const goNext = () => dispatch({ type: 'NAVIGATE_TO', index: state.currentStepIndex + 1 })
  const goPrev = () => dispatch({ type: 'NAVIGATE_TO', index: state.currentStepIndex - 1 })
  const navigateTo = (index) => dispatch({ type: 'NAVIGATE_TO', index })

  return (
    <PipelineContext.Provider
      value={{
        ...state,
        isStepUnlocked,
        isStepActive,
        startStep,
        completeStep,
        errorStep,
        skipStep,
        goNext,
        goPrev,
        navigateTo,
        dispatch,
      }}
    >
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline() {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error('usePipeline must be used inside PipelineProvider')
  return ctx
}
