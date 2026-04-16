import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import HeroSection from '../components/HeroSection'
import ScanForm from '../components/ScanForm'
import ScanCard from '../components/ScanCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { listScans } from '../api/client'
import { Lock, RefreshCw } from 'lucide-react'

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

export default function Dashboard() {
  const [scans, setScans]     = useState([])
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
    const interval = setInterval(fetchScans, 5000)
    return () => clearInterval(interval)
  }, [fetchScans])

  const handleScanCreated = (scan) => {
    setScans((prev) => [scan, ...prev])
    const interval = setInterval(async () => {
      const fresh = await listScans(0, 10)
      setScans(fresh)
      const stillRunning = fresh.some((s) => s.status === 'queued' || s.status === 'running')
      if (!stillRunning) clearInterval(interval)
    }, 3000)
  }

  const handleDelete = (id) => setScans((prev) => prev.filter((s) => s.id !== id))

  return (
    <>
      {/* Section A — Immersive intro */}
      <HeroSection />

      {/* Section B — Functional dashboard */}
      <section id="app" className="bg-surface-50 border-t border-surface-200">
        <div className="container mx-auto px-4 md:px-8 max-w-7xl py-16">

          {/* Section header */}
          <motion.div
            className="mb-12"
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-80px' }}
          >
            <div className="section-divider mb-4" />
            <h2 className="font-display text-3xl md:text-4xl font-bold text-surface-900 mb-2">
              Run a Scan
            </h2>
            <p className="text-surface-500 text-base">
              Submit a GitHub repository or upload a ZIP archive to begin analysis.
            </p>
          </motion.div>

          {/* Main grid */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">

            {/* Scan form */}
            <motion.div
              className="lg:col-span-2"
              variants={fadeUp}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: '-60px' }}
            >
              <ScanForm onScanCreated={handleScanCreated} />
            </motion.div>

            {/* Recent scans */}
            <motion.div
              className="lg:col-span-3"
              variants={fadeUp}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: 0.1 }}
            >
              <div className="flex items-center justify-between mb-5 px-1">
                <h3 className="font-display text-xl font-bold text-surface-900">Recent Scans</h3>
                <button
                  onClick={fetchScans}
                  className="btn-secondary text-xs px-3 py-1.5 rounded-lg"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Refresh
                </button>
              </div>

              {loading ? (
                <LoadingSpinner message="Loading scans..." />
              ) : scans.length === 0 ? (
                <div className="glass p-12 text-center border-dashed border-surface-300">
                  <Lock className="w-10 h-10 text-surface-300 mx-auto mb-3" />
                  <p className="text-surface-400 font-medium text-sm">
                    No scans yet. Submit your first repository above.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {scans.map((scan, i) => (
                    <motion.div
                      key={scan.id}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05, duration: 0.35 }}
                    >
                      <ScanCard scan={scan} onDelete={handleDelete} />
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </section>
    </>
  )
}
