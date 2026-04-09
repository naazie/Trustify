import { useState } from 'react'
import SeverityBadge from './SeverityBadge'

const TOOL_ICONS = {
  semgrep:  '🔬',
  gitleaks: '🔑',
  pylint:   '🐍',
}

export default function FindingRow({ finding, index }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`glass-hover border-l-2 ${
      finding.severity === 'critical' ? 'border-l-red-500' :
      finding.severity === 'warning'  ? 'border-l-amber-500' :
                                        'border-l-blue-500'
    } animate-fade-in`}
      style={{ animationDelay: `${index * 40}ms` }}
    >
      {/* Summary row */}
      <button
        id={`finding-row-${finding.id}`}
        className="w-full text-left p-4 flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Tool icon */}
        <span className="text-xl flex-shrink-0">{TOOL_ICONS[finding.tool] ?? '🔍'}</span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={finding.severity} />
            <span className="tool-badge">{finding.tool}</span>
            {finding.cwe && (
              <span className="text-xs text-slate-500 font-mono">{finding.cwe}</span>
            )}
          </div>
          <p className="text-sm font-semibold text-slate-200 truncate">{finding.title}</p>
          <p className="text-xs text-slate-500 font-mono mt-0.5 truncate">
            {finding.file_path}:{finding.line_start}
          </p>
        </div>

        {/* Impact score */}
        {finding.impact_score != null && (
          <div className="flex-shrink-0 text-right">
            <div className={`text-lg font-bold ${
              finding.impact_score >= 7 ? 'text-red-400' :
              finding.impact_score >= 4 ? 'text-amber-400' :
                                          'text-blue-400'
            }`}>
              {finding.impact_score.toFixed(1)}
            </div>
            <div className="text-[10px] text-slate-600">Impact</div>
          </div>
        )}

        {/* Expand chevron */}
        <span className={`text-slate-500 text-sm flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}>
          ›
        </span>
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-white/5 space-y-4 animate-fade-in">
          {/* Raw description */}
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Description</p>
            <p className="text-sm text-slate-300">{finding.description}</p>
          </div>

          {/* Code snippet */}
          {finding.code_snippet && (
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Code</p>
              <pre className="text-xs font-mono bg-surface-900 border border-white/5 rounded-lg p-3 overflow-x-auto text-slate-300">
                <code>{finding.code_snippet}</code>
              </pre>
            </div>
          )}

          {/* AI Plain English */}
          {finding.plain_english && (
            <div className="p-3 rounded-xl bg-brand-900/20 border border-brand-500/15">
              <p className="text-xs font-semibold text-brand-400 uppercase tracking-wide mb-1.5 flex items-center gap-1">
                ✨ AI Explanation
              </p>
              <p className="text-sm text-slate-300">{finding.plain_english}</p>
            </div>
          )}

          {/* AI Remediation */}
          {finding.remediation && (
            <div className="p-3 rounded-xl bg-emerald-900/10 border border-emerald-500/15">
              <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-1.5 flex items-center gap-1">
                🔧 Remediation Steps
              </p>
              <div className="text-sm text-slate-300 whitespace-pre-line">{finding.remediation}</div>
            </div>
          )}

          {/* Location info */}
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>📁 {finding.file_path}</span>
            <span>Lines {finding.line_start}–{finding.line_end}</span>
            <span className="font-mono">{finding.rule_id}</span>
          </div>
        </div>
      )}
    </div>
  )
}
