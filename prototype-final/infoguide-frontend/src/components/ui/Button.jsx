import { cn } from '../../utils/cn'

const variants = {
  primary: 'bg-blue-700 hover:bg-blue-800 text-white border border-blue-700',
  secondary: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300',
  ghost: 'bg-transparent hover:bg-slate-100 text-slate-600 border border-transparent',
  danger: 'bg-white hover:bg-red-50 text-red-600 border border-red-200',
}

export default function Button({ variant = 'primary', className, disabled, children, ...props }) {
  return (
    <button
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
