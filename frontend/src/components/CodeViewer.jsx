import { useState } from 'react'

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
      <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
        No file-level findings to display
      </div>
    )
  }

  const active = selectedFile ?? files[0]
  const activeFindings = byFile[active] ?? []
  const affectedLines = new Set(activeFindings.map((f) => f.line_start))

  return (
    <div className="flex flex-col gap-4">
      {/* File tabs */}
      <div className="flex gap-1 flex-wrap">
        {files.map((f) => (
          <button
            key={f}
            id={`file-tab-${f.replace(/\W/g, '-')}`}
            onClick={() => setSelectedFile(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 ${
              active === f
                ? 'bg-brand-600 text-white'
                : 'bg-surface-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            {f.split('/').pop()} ({byFile[f].length})
          </button>
        ))}
      </div>

      {/* File path */}
      <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
        <span>📁</span>
        <span>{active}</span>
      </div>

      {/* Finding list for selected file */}
      <div className="space-y-2">
        {activeFindings.map((f, i) => (
          <div
            key={f.id ?? i}
            className={`flex items-start gap-3 p-3 rounded-lg border ${
              f.severity === 'critical'
                ? 'bg-red-900/10 border-red-500/20'
                : f.severity === 'warning'
                ? 'bg-amber-900/10 border-amber-500/20'
                : 'bg-blue-900/10 border-blue-500/20'
            }`}
          >
            <div className={`flex-shrink-0 w-10 text-center py-0.5 rounded font-mono text-xs font-bold ${
              f.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
              f.severity === 'warning'  ? 'bg-amber-500/20 text-amber-400' :
                                          'bg-blue-500/20 text-blue-400'
            }`}>
              L{f.line_start}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-200">{f.title}</p>
              {f.code_snippet && (
                <pre className="text-xs font-mono text-slate-400 mt-1 overflow-x-auto whitespace-pre-wrap break-all">
                  {f.code_snippet}
                </pre>
              )}
              {f.plain_english && (
                <p className="text-xs text-slate-400 mt-1 italic">{f.plain_english}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
