import { useState, useEffect, useCallback } from 'react'
import ScanForm from '../components/ScanForm'
import ScanCard from '../components/ScanCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { listScans } from '../api/client'

const STATS = [
  { icon: '🔬', label: 'SAST Scanning',     desc: 'Semgrep auto-rules'    },
  { icon: '🔑', label: 'Secret Detection',  desc: 'Gitleaks patterns'     },
  { icon: '✨', label: 'AI Remediation',    desc: 'Gemini 2.0 Flash'      },
  { icon: '📊', label: 'Risk Metrics',      desc: 'Real-time dashboards'  },
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
    const hasRunning = scans.some((s) => s.status === 'queued' || s.status === 'running')
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
      <div className="text-center pt-4 pb-2">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-900/40 border border-brand-500/20 text-brand-300 text-xs font-medium mb-4">
          <span className="animate-pulse">⚡</span>
          AI-Powered · Shift-Left Security
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold mb-3">
          <span className="text-gradient">Trustify</span>
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto">
          Identify security flaws and leaked secrets in your source code before they reach production.
        </p>
      </div>

      {/* Feature pills */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {STATS.map(({ icon, label, desc }) => (
          <div key={label} className="glass p-4 flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <p className="text-sm font-semibold text-slate-200">{label}</p>
              <p className="text-xs text-slate-500">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Scan form */}
        <div className="lg:col-span-2">
          <ScanForm onScanCreated={handleScanCreated} />
        </div>

        {/* Recent scans */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-100">Recent Scans</h2>
            <button
              onClick={fetchScans}
              className="text-xs text-slate-500 hover:text-brand-400 transition-colors flex items-center gap-1"
            >
              ↻ Refresh
            </button>
          </div>

          {loading ? (
            <LoadingSpinner message="Loading scans..." />
          ) : scans.length === 0 ? (
            <div className="glass p-10 text-center">
              <div className="text-5xl mb-3">🔒</div>
              <p className="text-slate-400">No scans yet. Submit your first repository above.</p>
            </div>
          ) : (
            <div className="space-y-3">
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
