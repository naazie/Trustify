import { useState } from 'react'
import { FolderOpen, AlertCircle, AlertTriangle, Info, Sparkles } from 'lucide-react'

const SEVERITY_CONFIG = {
  critical: {
    row:    'bg-red-50 border-red-200',
    line:   'bg-red-100 text-red-700 border border-red-200',
    icon:   AlertCircle,
    iconCls: 'text-red-500',
  },
  warning: {
    row:    'bg-amber-50 border-amber-200',
    line:   'bg-amber-100 text-amber-700 border border-amber-200',
    icon:   AlertTriangle,
    iconCls: 'text-amber-500',
  },
  info: {
    row:    'bg-blue-50 border-blue-200',
    line:   'bg-blue-100 text-blue-700 border border-blue-200',
    icon:   Info,
    iconCls: 'text-blue-500',
  },
}

export default function CodeViewer({ findings }) {
  const [selectedFile, setSelectedFile] = useState(null)

  // Group findings by file
  const byFile = {}
  findings.forEach((f) => {
    if (!byFile[f.file_path]) byFile[f.file_path] = []
    byFile[f.file_path].push(f)
  })

  const files = Object.keys(byFile)

  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 text-sm font-medium">
        No file-level findings to display
      </div>
    )
  }

  const active = selectedFile ?? files[0]
  const activeFindings = byFile[active] ?? []

  return (
    <div className="flex flex-col gap-5">
      {/* File tabs */}
      <div className="flex gap-2 flex-wrap p-1 bg-slate-100 border border-slate-200 rounded-xl shadow-inner">
        {files.map((f) => {
          const count = byFile[f].length
          const hasCritical = byFile[f].some(x => x.severity === 'critical')
          return (
            <button
              key={f}
              id={`file-tab-${f.replace(/\W/g, '-')}`}
              onClick={() => setSelectedFile(f)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all duration-200 ${
                active === f
                  ? 'bg-white text-brand-700 border border-slate-200 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}
            >
              {f.split('/').pop()}
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                hasCritical ? 'bg-red-100 text-red-600' : 'bg-slate-200 text-slate-600'
              }`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* File path breadcrumb */}
      <div className="flex items-center gap-2 text-xs font-mono font-semibold text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
        <FolderOpen className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
        <span className="truncate">{active}</span>
        <span className="ml-auto flex-shrink-0 text-[10px] font-bold uppercase tracking-wide text-slate-400">
          {activeFindings.length} finding{activeFindings.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Finding list for selected file */}
      <div className="space-y-3">
        {activeFindings.map((f, i) => {
          const cfg = SEVERITY_CONFIG[f.severity] ?? SEVERITY_CONFIG.info
          const SevIcon = cfg.icon
          return (
            <div
              key={f.id ?? i}
              className={`flex items-start gap-4 p-4 rounded-xl border ${cfg.row} animate-slide-up`}
              style={{ animationDelay: `${i * 30}ms` }}
            >
              {/* Line + severity indicator */}
              <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
                <div className={`w-12 text-center py-1 rounded-lg font-mono text-xs font-bold ${cfg.line}`}>
                  L{f.line_start}
                </div>
                <SevIcon className={`w-4 h-4 ${cfg.iconCls}`} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <p className="text-sm font-bold text-slate-800">{f.title}</p>
                  {f.tool && (
                    <span className="tool-badge">{f.tool}</span>
                  )}
                </div>

                {f.code_snippet && (
                  <pre className="text-xs font-mono bg-slate-950 text-slate-300 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-all mt-2 border border-slate-800 shadow-inner leading-relaxed">
                    {f.code_snippet}
                  </pre>
                )}

                {f.plain_english && (
                  <div className="flex items-start gap-1.5 mt-2.5 bg-brand-50 border border-brand-200 rounded-lg px-3 py-2">
                    <Sparkles className="w-3.5 h-3.5 text-teal-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs font-medium text-slate-600 italic leading-relaxed">{f.plain_english}</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
