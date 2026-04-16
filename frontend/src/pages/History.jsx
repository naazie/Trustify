import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listScans, deleteScan } from '../api/client'
import { format } from 'date-fns'
import LoadingSpinner from '../components/LoadingSpinner'
import { ClipboardList, ArrowLeft, ArrowRight, X } from 'lucide-react'

const STATUS_COLORS = {
  queued:   'text-slate-500',
  running:  'text-brand-600',
  complete: 'text-emerald-600',
  failed:   'text-red-600',
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
          <h1 className="text-2xl font-bold text-slate-800">Scan History</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">All past security scans and their results</p>
        </div>
        <Link to="/" className="btn-primary text-sm shadow-sm py-2">
          + New Scan
        </Link>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading history..." />
      ) : scans.length === 0 ? (
        <div className="glass p-16 text-center border-dashed border-2">
          <div className="flex justify-center mb-4">
            <ClipboardList className="w-12 h-12 text-slate-300" />
          </div>
          <p className="text-slate-500 font-medium">No scan history yet.</p>
          <Link to="/" className="btn-primary mt-6 inline-flex">Start Your First Scan</Link>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="glass overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs text-slate-500 uppercase tracking-wide bg-slate-50/50">
                  <th className="text-left p-4 font-bold">Source</th>
                  <th className="text-left p-4 font-bold">Status</th>
                  <th className="text-left p-4 hidden md:table-cell font-bold">Languages</th>
                  <th className="text-center p-4 font-bold">Critical</th>
                  <th className="text-center p-4 font-bold">Warning</th>
                  <th className="text-center p-4 font-bold">Info</th>
                  <th className="text-left p-4 hidden md:table-cell font-bold">Date</th>
                  <th className="p-4"></th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {scans.map((scan, idx) => (
                  <tr
                    key={scan.id}
                    className="border-b border-slate-100 hover:bg-slate-50 transition-colors group"
                    style={{ animationDelay: `${idx * 20}ms` }}
                  >
                    <td className="p-4">
                      <Link
                        to={`/scan/${scan.id}`}
                        className="text-brand-600 hover:text-accent-500 font-mono text-xs truncate max-w-[200px] block transition-colors"
                      >
                        {scan.source_url
                          ? scan.source_url.replace('https://github.com/', '')
                          : scan.source_filename ?? scan.id}
                      </Link>
                    </td>
                    <td className="p-4">
                      <span className={`text-xs font-bold ${STATUS_COLORS[scan.status]}`}>
                        {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
                      </span>
                    </td>
                    <td className="p-4 hidden md:table-cell">
                      <div className="flex gap-1 flex-wrap">
                        {scan.languages.slice(0, 3).map((l) => (
                          <span key={l} className="tool-badge">{l}</span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      <span className="text-red-500 font-extrabold bg-red-50 px-2 py-1 rounded inline-block min-w-[2rem] border border-red-100">{scan.summary.critical || '0'}</span>
                    </td>
                    <td className="p-4 text-center">
                      <span className="text-amber-500 font-extrabold bg-amber-50 px-2 py-1 rounded inline-block min-w-[2rem] border border-amber-100">{scan.summary.warning || '0'}</span>
                    </td>
                    <td className="p-4 text-center">
                      <span className="text-blue-500 font-extrabold bg-blue-50 px-2 py-1 rounded inline-block min-w-[2rem] border border-blue-100">{scan.summary.info || '0'}</span>
                    </td>
                    <td className="p-4 text-xs font-medium text-slate-500 hidden md:table-cell">
                      {format(new Date(scan.created_at), 'MMM d, yyyy HH:mm')}
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2 pr-2">
                        <Link to={`/scan/${scan.id}`} className="btn-secondary py-1.5 px-3 text-xs bg-slate-50 border border-slate-200">View</Link>
                        <button
                          onClick={() => handleDelete(scan.id)}
                          className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 p-1.5 hover:bg-red-50 rounded-lg transition-all"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary disabled:opacity-50 text-sm py-2 px-4 shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>
            <span className="text-sm font-semibold text-slate-500">Page {page + 1}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={scans.length < PAGE_SIZE}
              className="btn-secondary disabled:opacity-50 text-sm py-2 px-4 shadow-sm"
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
