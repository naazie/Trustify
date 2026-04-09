import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listScans, deleteScan } from '../api/client'
import { format } from 'date-fns'
import LoadingSpinner from '../components/LoadingSpinner'
import SeverityBadge from '../components/SeverityBadge'

const STATUS_COLORS = {
  queued:   'text-slate-400',
  running:  'text-brand-400',
  complete: 'text-emerald-400',
  failed:   'text-red-400',
}

export default function History() {
  const [scans, setScans]   = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage]     = useState(0)
  const PAGE_SIZE = 15

  const fetchScans = async (p = 0) => {
    setLoading(true)
    try {
      const data = await listScans(p * PAGE_SIZE, PAGE_SIZE)
      setScans(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchScans(page) }, [page])

  const handleDelete = async (id) => {
    if (!confirm('Delete this scan?')) return
    await deleteScan(id)
    setScans((prev) => prev.filter((s) => s.id !== id))
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Scan History</h1>
          <p className="text-sm text-slate-500 mt-1">All past security scans and their results</p>
        </div>
        <Link to="/" className="btn-primary text-sm">
          + New Scan
        </Link>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading history..." />
      ) : scans.length === 0 ? (
        <div className="glass p-16 text-center">
          <div className="text-5xl mb-3">📋</div>
          <p className="text-slate-400">No scan history yet.</p>
          <Link to="/" className="btn-primary mt-4 inline-flex">Start Your First Scan</Link>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="glass overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5 text-xs text-slate-500 uppercase tracking-wide">
                  <th className="text-left p-4">Source</th>
                  <th className="text-left p-4">Status</th>
                  <th className="text-left p-4 hidden md:table-cell">Languages</th>
                  <th className="text-center p-4">Critical</th>
                  <th className="text-center p-4">Warning</th>
                  <th className="text-center p-4">Info</th>
                  <th className="text-left p-4 hidden md:table-cell">Date</th>
                  <th className="p-4"></th>
                </tr>
              </thead>
              <tbody>
                {scans.map((scan, idx) => (
                  <tr
                    key={scan.id}
                    className="border-b border-white/5 hover:bg-surface-700/30 transition-colors"
                    style={{ animationDelay: `${idx * 30}ms` }}
                  >
                    <td className="p-4">
                      <Link
                        to={`/scan/${scan.id}`}
                        className="text-brand-400 hover:text-brand-300 font-mono text-xs truncate max-w-[200px] block"
                      >
                        {scan.source_url
                          ? scan.source_url.replace('https://github.com/', '')
                          : scan.source_filename ?? scan.id}
                      </Link>
                    </td>
                    <td className="p-4">
                      <span className={`text-xs font-medium ${STATUS_COLORS[scan.status]}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="p-4 hidden md:table-cell">
                      <div className="flex gap-1 flex-wrap">
                        {scan.languages.slice(0, 3).map((l) => (
                          <span key={l} className="tool-badge">{l}</span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4 text-center text-red-400 font-bold">
                      {scan.summary.critical || '—'}
                    </td>
                    <td className="p-4 text-center text-amber-400 font-bold">
                      {scan.summary.warning || '—'}
                    </td>
                    <td className="p-4 text-center text-blue-400 font-bold">
                      {scan.summary.info || '—'}
                    </td>
                    <td className="p-4 text-xs text-slate-500 hidden md:table-cell">
                      {format(new Date(scan.created_at), 'MMM d, yyyy HH:mm')}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Link to={`/scan/${scan.id}`} className="btn-secondary py-1 px-3 text-xs">View</Link>
                        <button
                          onClick={() => handleDelete(scan.id)}
                          className="btn-danger py-1 px-2 text-xs"
                        >
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary disabled:opacity-40 text-sm py-2 px-4"
            >
              ← Previous
            </button>
            <span className="text-sm text-slate-500">Page {page + 1}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={scans.length < PAGE_SIZE}
              className="btn-secondary disabled:opacity-40 text-sm py-2 px-4"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
