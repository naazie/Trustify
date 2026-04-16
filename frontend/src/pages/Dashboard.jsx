import { useState, useEffect, useCallback } from 'react'
import ScanForm from '../components/ScanForm'
import ScanCard from '../components/ScanCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { listScans } from '../api/client'
import { Microscope, KeySquare, Sparkles, LineChart, Lock, RefreshCw, Zap } from 'lucide-react'

const STATS = [
  { icon: Microscope, label: 'SAST Scanning',     desc: 'Semgrep auto-rules'    },
  { icon: KeySquare,  label: 'Secret Detection',  desc: 'Gitleaks patterns'     },
  { icon: Sparkles,   label: 'AI Remediation',    desc: 'Gemini 2.0 Flash'      },
  { icon: LineChart,  label: 'Risk Metrics',      desc: 'Real-time dashboards'  },
]

export default function Dashboard() {
  const [scans, setScans]   = useState([])
  const [loading, setLoading] = useState(true)

  const fetchScans = useCallback(async () => {
    try {
      const data = await listScans(0, 10)
      setScans(data)
    } catch (e) {
      console.error('Failed to fetch scans:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScans()
    // Poll for running scans every 5 seconds
    const interval = setInterval(fetchScans, 5000)
    return () => clearInterval(interval)
  }, [fetchScans])

  const handleScanCreated = (scan) => {
    setScans((prev) => [scan, ...prev])
    // Poll more aggressively after new scan
    const interval = setInterval(async () => {
      const fresh = await listScans(0, 10)
      setScans(fresh)
      const stillRunning = fresh.some((s) => s.status === 'queued' || s.status === 'running')
      if (!stillRunning) clearInterval(interval)
    }, 3000)
  }

  const handleDelete = (id) => setScans((prev) => prev.filter((s) => s.id !== id))

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Hero */}
      <div className="text-center pt-8 pb-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-bold uppercase tracking-wide mb-6 shadow-sm">
          <Zap className="w-3.5 h-3.5 text-accent-500" />
          AI-Powered · Shift-Left Security
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold mb-4 text-slate-800">
          <span className="text-gradient">Trustify</span>
        </h1>
        <p className="text-slate-500 font-medium text-lg max-w-xl mx-auto">
          Identify security flaws and leaked secrets in your source code before they reach production.
        </p>
      </div>

      {/* Feature pills */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {STATS.map(({ icon: Icon, label, desc }) => (
          <div key={label} className="glass p-5 flex items-start gap-4">
            <div className="p-2.5 rounded-xl bg-brand-50 text-brand-600 border border-brand-100 shadow-sm">
               <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800">{label}</p>
              <p className="text-xs font-medium text-slate-500 mt-0.5">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Scan form */}
        <div className="lg:col-span-2">
          <ScanForm onScanCreated={handleScanCreated} />
        </div>

        {/* Recent scans */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-5 px-1">
            <h2 className="text-lg font-bold text-slate-800">Recent Scans</h2>
            <button
              onClick={fetchScans}
              className="text-xs font-bold uppercase tracking-wide text-slate-400 hover:text-brand-600 transition-colors flex items-center gap-1.5 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm hover:border-brand-200 hover:bg-brand-50"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>

          {loading ? (
            <LoadingSpinner message="Loading scans..." />
          ) : scans.length === 0 ? (
            <div className="glass p-12 text-center rounded-2xl border-dashed">
              <div className="flex justify-center mb-4">
                <Lock className="w-12 h-12 text-slate-300" />
              </div>
              <p className="text-slate-500 font-medium">No scans yet. Submit your first repository above.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {scans.map((scan) => (
                <ScanCard key={scan.id} scan={scan} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
