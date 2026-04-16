import { useState } from 'react'
import SeverityBadge from './SeverityBadge'
import { Microscope, KeyRound, Code2, Package, Search, ChevronRight, GitCommitHorizontal, Sparkles, Info, Wrench, FolderOpen } from 'lucide-react'

const TOOL_ICONS = {
  semgrep:  Microscope,
  gitleaks: KeyRound,
  pylint:   Code2,
  eslint:   Code2,
}

const TYPE_ICONS = {
  SECURITY:     KeyRound,
  SECRET:       KeyRound,
  CODE_QUALITY: Code2,
  DEPENDENCY:   Package,
}

export default function FindingRow({ finding, index }) {
  const [expanded, setExpanded] = useState(false)

  const borderColor =
    finding.severity === 'critical' ? 'border-l-red-500' :
    finding.severity === 'warning'  ? 'border-l-amber-500' :
                                       'border-l-blue-400'

  const ToolIcon = TOOL_ICONS[finding.tool] ?? Search
  const TypeIcon = TYPE_ICONS[finding.type] ?? Search

  return (
    <div
      className={`glass-hover border-l-2 ${borderColor} animate-fade-in`}
      style={{ animationDelay: `${index * 40}ms` }}
    >
      {/* ── Summary row ───────────────────────────────────────── */}
      <button
        className="w-full text-left p-4 flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500">
          <TypeIcon className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={finding.severity} />
            <span className="tool-badge"><ToolIcon className="w-3 h-3" />{finding.tool}</span>
            {finding.subcategory && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-500 font-mono">
                {finding.subcategory.replace(/_/g, ' ')}
              </span>
            )}
            {finding.cwe && (
              <span className="text-xs text-amber-600 font-mono font-bold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">{finding.cwe}</span>
            )}
            {finding.found_in_history && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-purple-50 text-purple-600 border border-purple-200 font-medium flex items-center gap-1">
                <GitCommitHorizontal className="w-3 h-3" /> history
              </span>
            )}
          </div>
          <p className="text-sm font-bold text-slate-800 truncate">{finding.title}</p>
          <p className="text-xs font-mono font-medium text-slate-500 mt-0.5 truncate">
            {finding.file_path}:{finding.line_start}
          </p>
        </div>

        {/* Confidence + Impact */}
        <div className="flex-shrink-0 text-right space-y-0.5">
          {finding.impact_score != null && (
            <div>
              <div className={`text-lg font-extrabold ${
                finding.impact_score >= 7 ? 'text-red-600' :
                finding.impact_score >= 4 ? 'text-amber-600' :
                                             'text-blue-600'
              }`}>
                {finding.impact_score.toFixed(1)}
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Impact</div>
            </div>
          )}
          {finding.confidence != null && (
            <div className="text-[10px] font-bold text-slate-400">
              {Math.round(finding.confidence * 100)}% conf.
            </div>
          )}
        </div>

        <ChevronRight className={`text-slate-400 w-4 h-4 flex-shrink-0 mt-1 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {/* ── Expanded panel ────────────────────────────────────── */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 space-y-4 animate-fade-in">

          {/* Raw description */}
          <div className="pt-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Description</p>
            <p className="text-sm text-slate-700 leading-relaxed">{finding.description}</p>
          </div>

          {/* Code snippet */}
          {finding.code_snippet && (
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Code</p>
              <pre className="text-xs font-mono bg-slate-950 text-slate-200 border border-slate-800 rounded-xl p-4 overflow-x-auto shadow-inner">
                <code>{finding.code_snippet}</code>
              </pre>
            </div>
          )}

          {/* Commit history (Gitleaks) */}
          {finding.commit_history && finding.commit_history.length > 0 && (
            <div className="p-3 rounded-xl bg-purple-50 border border-purple-200">
              <p className="text-xs font-bold text-purple-700 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
                <GitCommitHorizontal className="w-3.5 h-3.5" /> Found in Git Commits
              </p>
              <div className="flex flex-wrap gap-2">
                {finding.commit_history.map((c, i) => (
                  <span key={i} className="text-xs font-mono bg-white text-purple-600 px-2 py-0.5 rounded border border-purple-200 shadow-sm">
                    {c.slice(0, 8)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI Plain English */}
          {finding.plain_english && (
            <div className="p-4 rounded-xl bg-brand-50 border border-brand-200">
              <p className="text-xs font-bold text-brand-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-accent-500" /> Plain English
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">{finding.plain_english}</p>
              {finding.why_it_matters && (
                <p className="text-xs font-semibold text-amber-700 mt-2.5 italic flex items-start gap-1.5">
                  <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />{finding.why_it_matters}
                </p>
              )}
            </div>
          )}

          {/* What it means */}
          {finding.what_it_means && finding.what_it_means.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2">
                What it means
              </p>
              <ul className="space-y-1.5">
                {finding.what_it_means.map((point, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 flex-shrink-0 mt-2" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* How to fix */}
          {finding.how_to_fix && finding.how_to_fix.length > 0 && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
              <p className="text-xs font-bold text-emerald-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Wrench className="w-3.5 h-3.5" /> How to fix
              </p>
              <ol className="space-y-2 list-none">
                {finding.how_to_fix.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm text-slate-700">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold shadow-sm">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Location info */}
          <div className="flex items-center flex-wrap gap-4 text-xs font-medium text-slate-500 pt-1 border-t border-slate-100">
            <span className="flex items-center gap-1"><FolderOpen className="w-3.5 h-3.5" /> {finding.file_path}</span>
            <span>Lines {finding.line_start}–{finding.line_end}</span>
            <span className="font-mono">{finding.rule_id}</span>
            {finding.type && <span className="font-mono">{finding.type}</span>}
          </div>
        </div>
      )}
    </div>
  )
}
