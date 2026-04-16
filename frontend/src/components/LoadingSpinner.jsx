export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-5 animate-fade-in">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-slate-200 border-t-brand-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <img src="/logo.png" alt="Loading" className="w-8 h-8 object-contain" />
        </div>
      </div>
      <p className="text-slate-500 text-sm font-semibold">{message}</p>
    </div>
  )
}

