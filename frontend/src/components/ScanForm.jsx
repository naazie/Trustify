import { useState, useRef } from 'react'
import { createScan, uploadScan } from '../api/client'

export default function ScanForm({ onScanCreated }) {
  const [mode, setMode]         = useState('github')  // 'github' | 'zip'
  const [url, setUrl]           = useState('')
  const [file, setFile]         = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef()

  const placeholder = 'https://github.com/owner/repository'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let scan
      if (mode === 'github') {
        if (!url.startsWith('https://github.com/')) {
          setError('Please enter a valid GitHub repository URL')
          setLoading(false)
          return
        }
        scan = await createScan({ source_type: 'github', source_url: url })
      } else {
        if (!file) { setError('Please select a ZIP file'); setLoading(false); return }
        const fd = new FormData()
        fd.append('file', file)
        scan = await uploadScan(fd)
      }
      onScanCreated(scan)
      setUrl('')
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to start scan. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped?.name.endsWith('.zip')) setFile(dropped)
    else setError('Only .zip files are supported')
  }

  return (
    <div className="glass p-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center text-xl shadow-lg shadow-brand-600/30">
          🔍
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100">New Security Scan</h2>
          <p className="text-xs text-slate-500">Semgrep · Gitleaks · Pylint · AI Remediation</p>
        </div>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1 p-1 bg-surface-700/50 rounded-xl mb-5 w-fit">
        {['github', 'zip'].map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => { setMode(m); setError('') }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              mode === m
                ? 'bg-brand-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {m === 'github' ? '🔗 GitHub URL' : '📦 Upload ZIP'}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'github' ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Repository URL
            </label>
            <input
              id="scan-github-url"
              type="url"
              className="input"
              placeholder={placeholder}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <p className="text-xs text-slate-600 mt-1.5">
              Public GitHub repositories. Cloned at scan time with no credentials stored.
            </p>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              ZIP Archive
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                dragOver
                  ? 'border-brand-500 bg-brand-500/5'
                  : file
                  ? 'border-emerald-500/40 bg-emerald-500/5'
                  : 'border-white/10 hover:border-brand-500/40 hover:bg-surface-700/30'
              }`}
            >
              <div className="text-3xl mb-2">{file ? '✅' : '📁'}</div>
              <p className="text-sm text-slate-300 font-medium">
                {file ? file.name : 'Drop a .zip file here or click to browse'}
              </p>
              {file && (
                <p className="text-xs text-slate-500 mt-1">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".zip"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-900/20 border border-red-500/20 text-red-400 text-sm">
            <span>⚠️</span> {error}
          </div>
        )}

        <button id="scan-submit-btn" type="submit" disabled={loading} className="btn-primary w-full justify-center">
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Initiating Scan...
            </>
          ) : (
            <>🚀 Start Security Scan</>
          )}
        </button>
      </form>
    </div>
  )
}
