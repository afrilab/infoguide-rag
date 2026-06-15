import { cn } from '../../utils/cn'

const styles = {
  idle: 'bg-slate-100 text-slate-500 border-slate-200',
  loading: 'bg-blue-50 text-blue-700 border-blue-200',
  done: 'bg-green-50 text-green-700 border-green-200',
  skipped: 'bg-slate-50 text-slate-500 border-slate-200',
  error: 'bg-red-50 text-red-600 border-red-200',
}

const labels = {
  idle: 'Pending',
  loading: 'Processing',
  done: 'Complete',
  skipped: 'Skipped',
  error: 'Error',
}

export default function Badge({ status = 'idle', className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full border',
        styles[status] ?? styles.idle,
        className
      )}
    >
      {status === 'loading' && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
      )}
      {status === 'done' && (
        <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
          <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      {labels[status] ?? status}
    </span>
  )
}
