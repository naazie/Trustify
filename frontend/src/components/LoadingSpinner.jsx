export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 animate-fade-in">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-surface-600 border-t-brand-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center text-2xl">🛡️</div>
      </div>
      <p className="text-slate-400 text-sm">{message}</p>
    </div>
  )
}
