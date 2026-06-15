import Spinner from './Spinner'
import Badge from './Badge'
import { cn } from '../../utils/cn'

function StepIndicator({ num, status }) {
  if (status === 'loading') {
    return (
      <div className="w-9 h-9 shrink-0 rounded-full border-2 border-blue-200 bg-white flex items-center justify-center">
        <Spinner size="sm" />
      </div>
    )
  }
  if (status === 'done' || status === 'skipped') {
    return (
      <div className="w-9 h-9 shrink-0 rounded-full bg-green-600 flex items-center justify-center">
        <svg className="w-4 h-4 text-white" viewBox="0 0 16 16" fill="none">
          <path d="M3 8l3.5 3.5 6.5-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    )
  }
  if (status === 'error') {
    return (
      <div className="w-9 h-9 shrink-0 rounded-full bg-red-500 flex items-center justify-center">
        <span className="text-white text-sm font-bold">!</span>
      </div>
    )
  }
  return (
    <div className="w-9 h-9 shrink-0 rounded-full bg-slate-800 text-white flex items-center justify-center text-sm font-semibold">
      {String(num).padStart(2, '0')}
    </div>
  )
}

export default function StepCard({ stepNum, title, subtitle, status, children }) {
  const isActive = status === 'idle' || status === 'loading' || status === 'error'
  const isDone = status === 'done' || status === 'skipped'

  return (
    <div className={cn(
      'border rounded-xl bg-white transition-colors',
      isActive && 'border-blue-500 shadow-sm shadow-blue-100',
      isDone && 'border-green-200',
      status === 'error' && 'border-red-300',
    )}>
      <div className="flex items-center justify-between px-5 py-3">
        <div className="flex items-center gap-4 min-w-0">
          <StepIndicator num={stepNum} status={status} />
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-slate-900 leading-tight">{title}</h2>
            {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>
        <Badge status={status} className="shrink-0 ml-4" />
      </div>

      <div className="px-5 pb-5 border-t border-slate-100">
        <div className="pt-4">{children}</div>
      </div>
    </div>
  )
}
