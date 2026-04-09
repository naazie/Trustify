import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getScan, getFindings } from '../api/client'
import RiskChart from '../components/RiskChart'
import FindingRow from '../components/FindingRow'
import CodeViewer from '../components/CodeViewer'
import LoadingSpinner from '../components/LoadingSpinner'
import SeverityBadge from '../components/SeverityBadge'
import { formatDistanceToNow, format } from 'date-fns'

const VIEWS = ['Findings', 'File Drilldown']
const SEVERITY_FILTERS = ['all', 'critical', 'warning', 'info']
const TOOL_ICONS = { semgrep: '🔬', gitleaks: '🔑', pylint: '🐍' }

export default function ScanDetail() {
  const { id }   = useParams()
  const [scan, setScan]         = useState(null)
  const [findings, setFindings] = useState([])
  const [loading, setLoading]   = useState(true)
  const [view, setView]         = useState('Findings')
  const [sevFilter, setSevFilter] = useState('all')
  const [toolFilter, setToolFilter] = useState('all')

  const fetchData = useCallback(async () => {
    try {
      const [scanData, findData] = await Promise.all([
        getScan(id),
        getFindings(id),
      ])
      setScan(scanData)
      setFindings(findData)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchData()
    const interval = setInterval(async () => {
      const s = await getScan(id)
      setScan(s)
      if (s.status === 'complete' || s.status === 'failed') {
        const f = await getFindings(id)
        setFindings(f)
        clearInterval(interval)
      }
    }, 4000)
    return () => clearInterval(interval)
  }, [fetchData])

  const filtered = findings.filter((f) => {
    if (sevFilter !== 'all'  && f.severity !== sevFilter) return false
    if (toolFilter !== 'all' && f.tool !== toolFilter)    return false
    return true
  })

  const tools = [...new Set(findings.map((f) => f.tool))]

  if (loading) return <LoadingSpinner message="Loading scan results..." />
  if (!scan)   return <div className="text-center py-20 text-slate-500">Scan not found</div>

  const isRunning = scan.status === 'queued' || scan.status === 'running'

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + header */}
      <div>
        <Link to="/" className="text-xs text-slate-500 hover:text-brand-400 transition-colors mb-3 inline-flex items-center gap-1">
          ← Back to Dashboard
        </Link>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 mb-1">
              Scan Results
            </h1>
            <p className="text-sm text-slate-500 font-mono">
              {scan.source_url ?? scan.source_filename ?? id}
            </p>
            <p className="text-xs text-slate-600 mt-1">
              {format(new Date(scan.created_at), 'PPpp')}
            </p>
          </div>
          <div className={`text-sm px-3 py-1.5 rounded-lg border font-medium ${
            scan.status === 'complete' ? 'bg-emerald-900/30 border-emerald-500/20 text-emerald-400' :
            scan.status === 'failed'   ? 'bg-red-900/30 border-red-500/20 text-red-400'            :
                                         'bg-brand-900/30 border-brand-500/20 text-brand-400'
          }`}>
            {isRunning && <span className="inline-block w-2 h-2 rounded-full bg-current mr-2 animate-pulse" />}
            {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
          </div>
        </div>
      </div>

      {/* Running state */}
      {isRunning && (
        <div className="glass p-6 flex items-center gap-4 border border-brand-500/20">
          <div className="w-10 h-10 border-4 border-surface-600 border-t-brand-500 rounded-full animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-brand-300">Scan In Progress</p>
            <p className="text-xs text-slate-500">Running security tools — this may take 1–3 minutes</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {scan.status === 'failed' && (
        <div className="glass p-4 border border-red-500/20 text-red-400 text-sm">
          ❌ {scan.error_message ?? 'Scan failed. Check backend logs for details.'}
        </div>
      )}

      {/* Metrics row */}
      {scan.status === 'complete' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Doughnut */}
          <div className="glass p-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Risk Overview</p>
            <RiskChart summary={scan.summary} />
          </div>

          {/* Stat cards */}
          <div className="md:col-span-3 grid grid-cols-3 gap-4">
            {[
              { label: 'Critical', val: scan.summary.critical, color: 'text-red-400',   bg: 'from-red-900/20'   },
              { label: 'Warning',  val: scan.summary.warning,  color: 'text-amber-400', bg: 'from-amber-900/20' },
              { label: 'Info',     val: scan.summary.info,     color: 'text-blue-400',  bg: 'from-blue-900/20'  },
            ].map(({ label, val, color, bg }) => (
              <div key={label} className={`glass p-5 bg-gradient-to-br ${bg} to-transparent`}>
                <p className="text-xs text-slate-500 mb-1">{label}</p>
                <p className={`text-4xl font-extrabold ${color}`}>{val}</p>
              </div>
            ))}
            {/* Languages + Tools */}
            <div className="glass p-5 col-span-3">
              <div className="flex gap-6">
                <div>
                  <p className="text-xs text-slate-500 mb-2">Languages Detected</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {scan.languages.map((l) => <span key={l} className="tool-badge">{l}</span>)}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-2">Tools Executed</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {scan.tools_run.map((t) => (
                      <span key={t} className="tool-badge">{TOOL_ICONS[t] ?? '🔍'} {t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View tabs */}
      {findings.length > 0 && (
        <>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex gap-1 p-1 bg-surface-700/40 rounded-xl w-fit">
              {VIEWS.map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    view === v ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>

            {/* Filters */}
            {view === 'Findings' && (
              <div className="flex gap-2 flex-wrap">
                <select
                  id="severity-filter"
                  value={sevFilter}
                  onChange={(e) => setSevFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-700 border border-white/10 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  {SEVERITY_FILTERS.map((s) => (
                    <option key={s} value={s}>{s === 'all' ? 'All Severities' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
                <select
                  id="tool-filter"
                  value={toolFilter}
                  onChange={(e) => setToolFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-surface-700 border border-white/10 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="all">All Tools</option>
                  {tools.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <span className="text-xs text-slate-500 self-center">{filtered.length} findings</span>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="glass p-4">
            {view === 'Findings' ? (
              filtered.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No findings match your filters</div>
              ) : (
                <div className="space-y-2">
                  {filtered.map((f, i) => <FindingRow key={f.id ?? i} finding={f} index={i} />)}
                </div>
              )
            ) : (
              <CodeViewer findings={findings} />
            )}
          </div>
        </>
      )}
    </div>
  )
}
