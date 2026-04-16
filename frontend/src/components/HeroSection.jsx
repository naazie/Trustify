import { useEffect, useState } from 'react'
import { motion, useAnimation, AnimatePresence } from 'framer-motion'
import { Shield, Microscope, KeySquare, Sparkles, LineChart, ChevronDown, ShieldCheck, AlertTriangle, Info } from 'lucide-react'

/* ── Animated terminal lines ── */
const TERMINAL_LINES = [
  { delay: 0.4,  color: 'text-emerald-400', text: '$ trustify scan https://github.com/acme/api' },
  { delay: 1.0,  color: 'text-stone-400',   text: '  ✓ Cloning repository...' },
  { delay: 1.6,  color: 'text-stone-400',   text: '  ✓ Running Semgrep (SAST)...' },
  { delay: 2.2,  color: 'text-stone-400',   text: '  ✓ Running Gitleaks (secrets)...' },
  { delay: 2.8,  color: 'text-stone-400',   text: '  ✓ Running Pylint + ESLint...' },
  { delay: 3.4,  color: 'text-amber-400',   text: '  ⚠  3 critical findings detected' },
  { delay: 4.0,  color: 'text-blue-400',    text: '  ✦ Gemini AI generating remediation...' },
  { delay: 4.6,  color: 'text-emerald-400', text: '  ✓ Report ready.' },
]

/* ── Floating finding badges ── */
const BADGES = [
  { icon: AlertTriangle, label: 'SQL Injection',      sev: 'critical', x: '8%',  y: '22%', delay: 0.8  },
  { icon: KeySquare,     label: 'Leaked API Key',     sev: 'critical', x: '78%', y: '15%', delay: 1.4  },
  { icon: AlertTriangle, label: 'XSS Vulnerability',  sev: 'warning',  x: '82%', y: '62%', delay: 2.0  },
  { icon: Info,          label: 'Unused Variable',    sev: 'info',     x: '5%',  y: '68%', delay: 2.6  },
  { icon: ShieldCheck,   label: 'Hardcoded Secret',   sev: 'critical', x: '70%', y: '82%', delay: 1.8  },
]

const SEV_STYLE = {
  critical: 'bg-red-50 border-red-200 text-red-700',
  warning:  'bg-amber-50 border-amber-200 text-amber-700',
  info:     'bg-blue-50 border-blue-200 text-blue-700',
}

/* ── Animated counter ── */
function Counter({ to, duration = 1.8 }) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    let start = null
    const step = (ts) => {
      if (!start) start = ts
      const progress = Math.min((ts - start) / (duration * 1000), 1)
      setVal(Math.floor(progress * to))
      if (progress < 1) requestAnimationFrame(step)
    }
    const raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [to, duration])
  return <>{val.toLocaleString()}</>
}

/* ── Terminal line with typewriter ── */
function TerminalLine({ text, color, delay }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay * 1000)
    return () => clearTimeout(t)
  }, [delay])
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className={`font-mono text-xs leading-6 ${color}`}
        >
          {text}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
}
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.12 } } }

export default function HeroSection() {
  return (
    <section className="hero-bg min-h-screen flex flex-col items-center justify-center px-4 pt-20 pb-16 relative overflow-hidden">

      {/* ── Background blobs ── */}
      <motion.div
        className="absolute top-10 left-[5%] w-80 h-80 rounded-full bg-brand-400/10 blur-3xl pointer-events-none"
        animate={{ scale: [1, 1.2, 1], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 9, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute bottom-16 right-[5%] w-96 h-96 rounded-full bg-accent-400/8 blur-3xl pointer-events-none"
        animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 11, repeat: Infinity, ease: 'easeInOut', delay: 3 }}
      />

      {/* ── Floating finding badges ── */}
      {BADGES.map(({ icon: Icon, label, sev, x, y, delay }) => (
        <motion.div
          key={label}
          className={`absolute hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold shadow-sm backdrop-blur-sm bg-white/80 ${SEV_STYLE[sev]}`}
          style={{ left: x, top: y }}
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{
            opacity: 1, scale: 1,
            y: [0, -6, 0],
          }}
          transition={{
            opacity: { delay, duration: 0.4 },
            scale:   { delay, duration: 0.4 },
            y: { delay: delay + 0.4, duration: 3 + delay * 0.3, repeat: Infinity, ease: 'easeInOut' },
          }}
        >
          <Icon className="w-3 h-3" />
          {label}
        </motion.div>
      ))}

      {/* ── Main content ── */}
      <motion.div
        className="max-w-2xl mx-auto text-center z-10"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        {/* Eyebrow badge */}
        <motion.div variants={fadeUp} className="mb-7 inline-flex">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-brand-200 text-brand-700 text-xs font-semibold uppercase tracking-widest shadow-sm">
            <Shield className="w-3.5 h-3.5 text-brand-500" />
            AI-Powered Security Orchestration
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          variants={fadeUp}
          className="font-display text-5xl md:text-[4.2rem] font-bold leading-[1.1] mb-5 text-surface-900"
        >
          Secure your code{' '}
          <span className="shimmer-text">before it ships.</span>
        </motion.h1>

        {/* Sub */}
        <motion.p
          variants={fadeUp}
          className="text-surface-500 text-lg font-light max-w-lg mx-auto mb-12 leading-relaxed"
        >
          Scan GitHub repos and ZIP archives for vulnerabilities, leaked secrets, and code quality issues — with AI-powered plain-English remediation.
        </motion.p>

        {/* ── Stat counters ── */}
        <motion.div
          variants={fadeUp}
          className="grid grid-cols-3 gap-4 mb-12 max-w-md mx-auto"
        >
          {[
            { value: 40,   suffix: '+',  label: 'Security Rules' },
            { value: 4,    suffix: '',   label: 'Analysis Tools' },
            { value: 100,  suffix: '%',  label: 'AI Explained' },
          ].map(({ value, suffix, label }) => (
            <div key={label} className="glass py-4 px-2 text-center">
              <div className="font-display text-3xl font-bold text-brand-700">
                <Counter to={value} />{suffix}
              </div>
              <div className="text-xs text-surface-400 mt-1 font-medium">{label}</div>
            </div>
          ))}
        </motion.div>

        {/* ── Terminal window ── */}
        <motion.div
          variants={fadeUp}
          className="rounded-2xl overflow-hidden border border-surface-200 shadow-xl text-left"
        >
          {/* Title bar */}
          <div className="bg-surface-800 px-4 py-3 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-400" />
            <span className="w-3 h-3 rounded-full bg-amber-400" />
            <span className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="ml-3 text-xs text-stone-400 font-mono">trustify — scan</span>
          </div>
          {/* Terminal body */}
          <div className="bg-surface-900 px-5 py-4 min-h-[200px]">
            {TERMINAL_LINES.map((line) => (
              <TerminalLine key={line.text} {...line} />
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Scroll cue */}
      <motion.a
        href="#app"
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-surface-400 hover:text-brand-600 transition-colors z-10"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        <span className="text-[10px] font-semibold tracking-widest uppercase">Start Scanning</span>
        <ChevronDown className="w-4 h-4" />
      </motion.a>
    </section>
  )
}
