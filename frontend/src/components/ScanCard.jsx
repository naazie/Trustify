import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import SeverityBadge from './SeverityBadge'
import { deleteScan } from '../api/client'

const STATUS_CONFIG = {
  queued:   { cls: 'status-queued',   icon: '⏳', pulse: false },
  running:  { cls: 'status-running',  icon: '⚡', pulse: true  },
  complete: { cls: 'status-complete', icon: '✅', pulse: false },
  failed:   { cls: 'status-failed',   icon: '❌', pulse: false },
}

export default function ScanCard({ scan, onDelete }) {
  const cfg = STATUS_CONFIG[scan.status] ?? STATUS_CONFIG.queued
  const timeAgo = formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })
  const source = scan.source_url ?? scan.source_filename ?? 'Unknown source'

  const handleDelete = async (e) => {
    e.preventDefault()
    if (!confirm('Delete this scan and all its findings?')) return
    await deleteScan(scan.id)
    onDelete?.(scan.id)
  }

  return (
    <Link to={`/scan/${scan.id}`} className="block glass-hover p-5 animate-slide-up">
      <div className="flex items-start justify-between gap-3">
        {/* Left */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={cfg.cls}>
              <span className={cfg.pulse ? 'animate-pulse' : ''}>{cfg.icon}</span>
              {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
            </span>
            {scan.languages.slice(0, 4).map((l) => (
              <span key={l} className="tool-badge">{l}</span>
            ))}
          </div>
          <p className="text-sm text-slate-200 font-medium truncate">{source}</p>
          <p className="text-xs text-slate-500 mt-1">{timeAgo}</p>
        </div>

        {/* Summary bubbles */}
        {scan.status === 'complete' && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {scan.summary.critical > 0 && (
              <div className="text-center">
                <div className="text-lg font-bold text-red-400">{scan.summary.critical}</div>
                <div className="text-[10px] text-slate-500">Critical</div>
              </div>
            )}
            {scan.summary.warning > 0 && (
              <div className="text-center">
                <div className="text-lg font-bold text-amber-400">{scan.summary.warning}</div>
                <div className="text-[10px] text-slate-500">Warning</div>
              </div>
            )}
            {scan.summary.info > 0 && (
              <div className="text-center">
                <div className="text-lg font-bold text-blue-400">{scan.summary.info}</div>
                <div className="text-[10px] text-slate-500">Info</div>
              </div>
            )}
          </div>
        )}

        {/* Delete button */}
        <button
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-900/30 text-slate-600 hover:text-red-400 transition-all"
          title="Delete scan"
        >✕</button>
      </div>

      {/* Tools used */}
      {scan.tools_run.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-2">
          <span className="text-xs text-slate-600">Tools:</span>
          {scan.tools_run.map((t) => (
            <span key={t} className="tool-badge">{t}</span>
          ))}
        </div>
      )}
    </Link>
  )
}
