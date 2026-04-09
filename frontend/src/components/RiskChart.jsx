import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const COLORS = {
  critical: { bg: 'rgba(239,68,68,0.85)',  border: 'rgba(239,68,68,1)'  },
  warning:  { bg: 'rgba(245,158,11,0.85)', border: 'rgba(245,158,11,1)' },
  info:     { bg: 'rgba(59,130,246,0.85)', border: 'rgba(59,130,246,1)' },
}

export default function RiskChart({ summary }) {
  const { critical = 0, warning = 0, info = 0 } = summary

  if (critical + warning + info === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-slate-500 gap-2">
        <span className="text-4xl">🎉</span>
        <p className="text-sm">No findings detected</p>
      </div>
    )
  }

  const data = {
    labels: ['Critical', 'Warning', 'Info'],
    datasets: [{
      data: [critical, warning, info],
      backgroundColor: [COLORS.critical.bg, COLORS.warning.bg, COLORS.info.bg],
      borderColor:     [COLORS.critical.border, COLORS.warning.border, COLORS.info.border],
      borderWidth: 1.5,
      hoverOffset: 6,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '72%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          padding: 16,
          font: { size: 12, family: 'Inter' },
          usePointStyle: true,
          pointStyleWidth: 8,
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => ` ${ctx.label}: ${ctx.raw} findings`,
        },
        backgroundColor: 'rgba(17,17,24,0.95)',
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 1,
      },
    },
  }

  const total = critical + warning + info

  return (
    <div className="relative">
      <div className="h-52">
        <Doughnut data={data} options={options} />
      </div>
      {/* Centre label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pb-8 pointer-events-none">
        <span className="text-3xl font-bold text-slate-100">{total}</span>
        <span className="text-xs text-slate-500">findings</span>
      </div>
    </div>
  )
}
