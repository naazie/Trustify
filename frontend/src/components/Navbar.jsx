import { Link, NavLink } from 'react-router-dom'

const navLinks = [
  { to: '/',        label: 'Dashboard' },
  { to: '/history', label: 'History'   },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-surface-900/80 backdrop-blur-md">
      <div className="container mx-auto px-4 md:px-6 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-lg shadow-lg shadow-brand-600/30 group-hover:shadow-brand-500/50 transition-all duration-300">
              🛡️
            </div>
            <div>
              <span className="text-lg font-bold text-gradient">Trustify</span>
              <p className="text-[10px] text-slate-500 leading-none -mt-0.5">Security Orchestration</p>
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
                  `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-brand-600/20 text-brand-300 border border-brand-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface-700'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Status indicator */}
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow"></span>
            <span className="hidden sm:inline">System Online</span>
          </div>
        </div>
      </div>
    </header>
  )
}
