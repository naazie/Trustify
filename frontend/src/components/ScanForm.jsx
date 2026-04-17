import { useState, useRef } from 'react'
import { createScan, uploadScan } from '../api/client'
import { Search, Link2, FileArchive, AlertTriangle, CheckCircle, UploadCloud, Rocket, Loader2 } from 'lucide-react'
import { GithubIcon as Github } from './Icons'
import { useAuth } from '../context/AuthContext'
import GitHubRepoList from './GitHubRepoList'

export default function ScanForm({ onScanCreated }) {
  const [mode, setMode]         = useState('github')  // 'github' | 'zip'
  const [url, setUrl]           = useState('')
  const [file, setFile]         = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [dragOver, setDragOver] = useState(false)
  const { user, githubLogin } = useAuth()
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
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-50 to-surface-100 flex items-center justify-center border border-brand-200 text-brand-600 shadow-sm">
          <Search className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-800">New Security Scan</h2>
          <p className="text-xs font-medium text-slate-500">Semgrep · Gitleaks · Pylint · AI Remediation</p>
        </div>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1 p-1 bg-slate-100 border border-slate-200 rounded-xl mb-5 w-fit shadow-inner">
        {['github', 'zip'].map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => { setMode(m); setError('') }}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
              mode === m
                ? 'bg-white text-brand-700 shadow-sm border border-slate-200'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            {m === 'github' ? <><Github className="w-4 h-4" /> GitHub</> : <><FileArchive className="w-4 h-4" /> Upload ZIP</>}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'github' ? (
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide">
                Repository Target
              </label>
              <div className="relative">
                <input
                  id="scan-github-url"
                  type="url"
                  className="input pr-12 focus:ring-brand-500/20"
                  placeholder={placeholder}
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {url ? (
                    <CheckCircle className="w-5 h-5 text-emerald-500 animate-in zoom-in duration-300" />
                  ) : (
                    <Github className="w-5 h-5 text-slate-300" />
                  )}
                </div>
              </div>
            </div>

            <div>
              {user?.github_connected ? (
                <div className="animate-in fade-in slide-in-from-top-2 duration-500">
                  <div className="flex items-center justify-between mb-3 px-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select from account</span>
                  </div>
                  <GitHubRepoList 
                    selectedUrl={url}
                    onSelect={(selectedUrl) => setUrl(selectedUrl)} 
                  />
                </div>
              ) : (
                <div className="p-8 border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50 text-center">
                  <Github className="w-10 h-10 text-slate-300 mx-auto mb-4" />
                  <h4 className="text-sm font-bold text-slate-700 mb-1">GitHub Not Connected</h4>
                  <p className="text-xs text-slate-500 mb-6 px-10">Connect your account to browse and scan private repositories effortlessly.</p>
                  <button
                    type="button"
                    onClick={githubLogin}
                    className="btn-primary w-full max-w-xs py-2.5 rounded-xl shadow-md"
                  >
                    <Github className="w-4 h-4" />
                    Connect GitHub
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">
              ZIP Archive
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 bg-slate-50/50 ${
                dragOver
                  ? 'border-brand-400 bg-brand-50'
                  : file
                  ? 'border-emerald-400 bg-emerald-50'
                  : 'border-slate-300 hover:border-brand-300 hover:bg-slate-100'
              }`}
            >
              <div className="flex justify-center mb-2">
                {file ? <CheckCircle className="w-8 h-8 text-emerald-500" /> : <UploadCloud className="w-8 h-8 text-slate-400" />}
              </div>
              <p className="text-sm text-slate-600 font-semibold">
                {file ? file.name : 'Drop a .zip file here or click to browse'}
              </p>
              {file && (
                <p className="text-xs font-medium text-slate-500 mt-1">
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
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm font-medium">
            <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
          </div>
        )}

        <button id="scan-submit-btn" type="submit" disabled={loading} className="btn-primary w-full justify-center text-base py-3">
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Initiating Scan...
            </>
          ) : (
            <>
              <Rocket className="w-5 h-5" /> Start Security Scan
            </>
          )}
        </button>
      </form>
    </div>
  )
}
