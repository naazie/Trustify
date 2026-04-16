export default function SeverityBadge({ severity, size = 'md' }) {
  const map = {
    critical: { cls: 'badge-critical', dot: 'bg-red-400',   label: 'Critical' },
    warning:  { cls: 'badge-warning',  dot: 'bg-amber-400',  label: 'Warning'  },
    info:     { cls: 'badge-info',     dot: 'bg-blue-400',   label: 'Info'     },
  }
  const { cls, dot, label } = map[severity] ?? map.info

  return (
    <span className={cls}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  )
}
