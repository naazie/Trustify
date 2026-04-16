import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Clock, Zap, CheckCircle2, XCircle, X } from 'lucide-react'

const STATUS_CONFIG = {
  queued:   { cls: 'status-queued',   icon: Clock, pulse: false },
  running:  { cls: 'status-running',  icon: Zap, pulse: true  },
  complete: { cls: 'status-complete', icon: CheckCircle2, pulse: false },
  failed:   { cls: 'status-failed',   icon: XCircle, pulse: false },
}

export default function ScanCard({ scan, onDelete }) {
  const cfg = STATUS_CONFIG[scan.status] ?? STATUS_CONFIG.queued
  const Icon = cfg.icon
  const timeAgo = formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })
  const source = scan.source_url ?? scan.source_filename ?? 'Unknown source'

  const handleDelete = async (e) => {
    e.preventDefault()
    if (!confirm('Delete this scan and all its findings?')) return
    await deleteScan(scan.id)
    onDelete?.(scan.id)
  }

  return (
    <Link to={`/scan/${scan.id}`} className="block glass-hover p-5 animate-slide-up relative group">
      <div className="flex items-start justify-between gap-3">
        {/* Left */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={cfg.cls}>
              <Icon className={`w-3.5 h-3.5 ${cfg.pulse ? 'animate-pulse' : ''}`} />
              {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
            </span>
            {scan.languages.slice(0, 4).map((l) => (
              <span key={l} className="tool-badge">{l}</span>
            ))}
          </div>
          <p className="text-sm text-slate-800 font-semibold truncate">{source}</p>
          <p className="text-xs text-slate-500 mt-1">{timeAgo}</p>
        </div>

        {/* Summary bubbles */}
        {scan.status === 'complete' && (
          <div className="flex items-center gap-2 flex-shrink-0 pr-6">
            {scan.summary.critical > 0 && (
              <div className="text-center bg-red-50 px-2 py-1 rounded-lg border border-red-100">
                <div className="text-lg font-bold text-red-600 leading-tight">{scan.summary.critical}</div>
                <div className="text-[10px] text-red-500 font-bold uppercase tracking-wide">Crit</div>
              </div>
            )}
            {scan.summary.warning > 0 && (
              <div className="text-center bg-amber-50 px-2 py-1 rounded-lg border border-amber-100">
                <div className="text-lg font-bold text-amber-600 leading-tight">{scan.summary.warning}</div>
                <div className="text-[10px] text-amber-500 font-bold uppercase tracking-wide">Warn</div>
              </div>
            )}
            {scan.summary.info > 0 && (
              <div className="text-center bg-blue-50 px-2 py-1 rounded-lg border border-blue-100">
                <div className="text-lg font-bold text-blue-600 leading-tight">{scan.summary.info}</div>
                <div className="text-[10px] text-blue-500 font-bold uppercase tracking-wide">Info</div>
              </div>
            )}
          </div>
        )}

        {/* Delete button */}
        <button
          onClick={handleDelete}
          className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all border border-transparent hover:border-red-200 shadow-sm"
          title="Delete scan"
        ><X className="w-4 h-4" /></button>
      </div>

      {/* Tools used */}
      {scan.tools_run.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Tools:</span>
          {scan.tools_run.map((t) => (
            <span key={t} className="tool-badge">{t}</span>
          ))}
        </div>
      )}
    </Link>
  )
}
