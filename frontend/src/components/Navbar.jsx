import { Link, NavLink } from 'react-router-dom'
import { Activity } from 'lucide-react'

const navLinks = [
  { to: '/',        label: 'Dashboard' },
  { to: '/history', label: 'History'   },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md shadow-sm">
      <div className="container mx-auto px-4 md:px-6 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-50 to-surface-100 flex items-center justify-center border border-slate-200 shadow-sm group-hover:shadow-md group-hover:border-brand-200 transition-all duration-300">
              <img src="/logo.png" alt="Bug Mascot" className="w-6 h-6 object-contain" />
            </div>
            <div>
              <span className="text-lg font-bold text-gradient">Trustify</span>
              <p className="text-[10px] text-slate-500 font-medium leading-none mt-0.5 tracking-wide uppercase">Security Scanner</p>
            </div>
          </Link>

          {/* Nav links */}
          <nav className="flex items-center gap-1">
            {navLinks.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end
                className={({ isActive }) =>
                  `px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Status indicator */}
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            <Activity className="w-3.5 h-3.5 text-emerald-500 animate-pulse-slow" />
            <span className="hidden sm:inline">System Online</span>
          </div>
        </div>
      </div>
    </header>
  )
}
