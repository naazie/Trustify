import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getScan, getFindings, getReportUrl, downloadReport } from '../api/client'
import RiskChart from '../components/RiskChart'
import FindingRow from '../components/FindingRow'
import CodeViewer from '../components/CodeViewer'
import LoadingSpinner from '../components/LoadingSpinner'
import { format } from 'date-fns'
import { ArrowLeft, FileText, Download, Loader2 } from 'lucide-react'

const VIEWS = ['Findings', 'File Drilldown']
const SEVERITY_FILTERS = ['all', 'critical', 'warning', 'info']
const TYPE_FILTERS = ['all', 'SECURITY', 'SECRET', 'CODE_QUALITY', 'DEPENDENCY']

export default function ScanDetail() {
  const { id } = useParams()
  const [scan, setScan]           = useState(null)
  const [findings, setFindings]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [view, setView]           = useState('Findings')
  const [sevFilter, setSevFilter] = useState('all')
  const [toolFilter, setToolFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [downloading, setDownloading] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [scanData, findData] = await Promise.all([getScan(id), getFindings(id)])
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
    if (sevFilter  !== 'all' && f.severity !== sevFilter)  return false
    if (toolFilter !== 'all' && f.tool     !== toolFilter) return false
    if (typeFilter !== 'all' && f.type     !== typeFilter) return false
    return true
  })

  const tools = [...new Set(findings.map((f) => f.tool))]

  const handleDownloadJSON = async () => {
    setDownloading(true)
    try { await downloadReport(id, 'json') } finally { setDownloading(false) }
  }

  if (loading) return <LoadingSpinner message="Loading scan results..." />
  if (!scan)   return <div className="text-center py-20 text-slate-500 font-medium">Scan not found</div>

  const isRunning = scan.status === 'queued' || scan.status === 'running'

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + header */}
      <div>
        <Link to="/" className="text-xs font-bold text-slate-500 hover:text-brand-600 transition-colors mb-3 inline-flex items-center gap-1.5 uppercase tracking-wide">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
        </Link>
        <div className="flex items-start justify-between gap-4 flex-wrap mt-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 mb-1">Scan Results</h1>
            <p className="text-sm text-slate-500 font-mono">
              {scan.source_url ?? scan.source_filename ?? id}
            </p>
            <p className="text-xs font-medium text-slate-400 mt-1">
              {format(new Date(scan.created_at), 'PPpp')}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Status badge */}
            <div className={`text-sm px-3 py-1.5 rounded-lg border font-bold flex items-center gap-2 ${
              scan.status === 'complete' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' :
              scan.status === 'failed'   ? 'bg-red-50 border-red-200 text-red-700' :
                                           'bg-brand-50 border-brand-200 text-brand-700'
            }`}>
              {isRunning && <span className="inline-block w-2 h-2 rounded-full bg-current animate-pulse" />}
              {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
            </div>

            {/* Report buttons — only when complete */}
            {scan.status === 'complete' && (
              <>
                <a
                  href={getReportUrl(id, 'html')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-brand-50 border border-brand-200 text-brand-700 hover:bg-brand-100 transition-colors font-semibold shadow-sm"
                >
                  <FileText className="w-4 h-4" /> View Report
                </a>
                <button
                  onClick={handleDownloadJSON}
                  disabled={downloading}
                  className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-teal-50 border border-teal-200 text-teal-700 hover:bg-teal-100 transition-colors font-semibold disabled:opacity-50 shadow-sm"
                >
                  {downloading
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Downloading…</>
                    : <><Download className="w-4 h-4" /> Download JSON</>}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Running state */}
      {isRunning && (
        <div className="glass p-6 flex items-center gap-4 border-l-4 border-brand-400 bg-brand-50/30">
          <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-brand-700">Scan In Progress</p>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Running security tools — this may take 1–3 minutes</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {scan.status === 'failed' && (
        <div className="glass p-4 border-l-4 border-red-400 bg-red-50/50 text-red-600 text-sm font-medium">
          {scan.error_message ?? 'Scan failed. Check backend logs for details.'}
        </div>
      )}

      {/* Metrics row */}
      {scan.status === 'complete' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass p-5">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-3">Risk Overview</p>
            <RiskChart summary={scan.summary} />
          </div>
          <div className="md:col-span-3 grid grid-cols-3 gap-4">
            {[
              { label: 'Critical', val: scan.summary.critical, color: 'text-red-600',   bg: 'from-red-50',   border: 'border-l-red-400'   },
              { label: 'Warning',  val: scan.summary.warning,  color: 'text-amber-600', bg: 'from-amber-50', border: 'border-l-amber-400' },
              { label: 'Info',     val: scan.summary.info,     color: 'text-blue-600',  bg: 'from-blue-50',  border: 'border-l-blue-400'  },
            ].map(({ label, val, color, bg, border }) => (
              <div key={label} className={`glass p-5 bg-gradient-to-br ${bg} to-white border-l-4 ${border}`}>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1">{label}</p>
                <p className={`text-4xl font-extrabold ${color}`}>{val}</p>
              </div>
            ))}
            <div className="glass p-5 col-span-3">
              <div className="flex gap-8 flex-wrap">
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Languages Detected</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {scan.languages.map((l) => <span key={l} className="tool-badge">{l}</span>)}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Tools Executed</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {scan.tools_run.map((t) => (
                      <span key={t} className="tool-badge">{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View tabs + filters */}
      {findings.length > 0 && (
        <>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex gap-1 p-1 bg-slate-100 border border-slate-200 rounded-xl w-fit shadow-inner">
              {VIEWS.map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                    view === v ? 'bg-white text-brand-700 border border-slate-200 shadow-sm' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>

            {view === 'Findings' && (
              <div className="flex gap-2 flex-wrap items-center">
                <select
                  value={sevFilter}
                  onChange={(e) => setSevFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-sm text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                >
                  {SEVERITY_FILTERS.map((s) => (
                    <option key={s} value={s}>{s === 'all' ? 'All Severities' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>

                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-sm text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                >
                  {TYPE_FILTERS.map((t) => (
                    <option key={t} value={t}>{t === 'all' ? 'All Types' : t.replace('_', ' ')}</option>
                  ))}
                </select>

                <select
                  value={toolFilter}
                  onChange={(e) => setToolFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-sm text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                >
                  <option value="all">All Tools</option>
                  {tools.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>

                <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">{filtered.length} findings</span>
              </div>
            )}
          </div>

          <div className="glass p-4 shadow-sm">
            {view === 'Findings' ? (
              filtered.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm font-medium">No findings match your filters</div>
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
