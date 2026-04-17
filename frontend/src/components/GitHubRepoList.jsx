import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, GitBranch, Lock, Globe, Calendar, RefreshCw } from 'lucide-react'
import { GithubIcon as Github } from './Icons'
import { listGithubRepos } from '../api/client'

export default function GitHubRepoList({ onSelect, selectedUrl }) {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchRepos()
  }, [])

  const fetchRepos = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await listGithubRepos()
      setRepos(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load repositories')
    } finally {
      setLoading(false)
    }
  }

  const filteredRepos = repos.filter(repo => 
    repo.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (repo.language && repo.language.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="flex flex-col gap-4">
      {/* Search Header */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text"
            placeholder="Search repositories..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 transition-all font-medium"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button 
          type="button"
          onClick={fetchRepos}
          className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-500 transition-colors"
          title="Refresh repositories"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* List Container */}
      <div className="relative min-h-[300px] max-h-[400px] overflow-y-auto border border-slate-100 rounded-xl bg-slate-50/30 custom-scrollbar">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white/50 backdrop-blur-[2px]">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
            <p className="text-xs font-bold text-slate-500 uppercase tracking-tighter italic">Syncing GitHub...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-red-500 text-sm font-medium mb-3">{error}</p>
            <button 
              type="button"
              onClick={fetchRepos} 
              className="text-xs font-bold text-brand-600 hover:underline uppercase tracking-widest"
            >
              Retry Connection
            </button>
          </div>
        ) : filteredRepos.length === 0 ? (
          <div className="p-12 text-center opacity-60">
            <Github className="w-10 h-10 mx-auto mb-2 text-slate-300" />
            <p className="text-slate-500 text-sm font-medium">No results found</p>
          </div>
        ) : (
          <div className="p-2 grid grid-cols-1 gap-1.5">
            {filteredRepos.map(repo => {
              const isActive = selectedUrl === repo.url
              return (
                <button
                  key={repo.id}
                  type="button"
                  onClick={() => onSelect(repo.url)}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all text-left group ${
                    isActive 
                      ? 'bg-brand-50 border-brand-200 ring-1 ring-brand-200' 
                      : 'bg-white border-slate-100 hover:border-brand-100 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <div className="flex items-center gap-1.5 font-bold text-slate-800 text-sm truncate">
                      {isActive && <div className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />}
                      <span className="truncate">{repo.full_name}</span>
                      {repo.private ? (
                        <Lock className="w-3 h-3 text-amber-500" />
                      ) : (
                        <Globe className="w-3 h-3 text-emerald-500" />
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                      {repo.language && (
                        <span className="flex items-center gap-1">
                          <div className="w-1 h-1 rounded-full bg-slate-300" />
                          {repo.language}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5" />
                        {new Date(repo.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <GitBranch className={`w-4 h-4 transition-colors ${isActive ? 'text-brand-500' : 'text-slate-300 group-hover:text-brand-400'}`} />
                </button>
              )
            })}
          </div>
        )}
      </div>
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest text-center">
        Selected repository will be scanned using your GitHub secure token.
      </p>
    </div>
  )
}
