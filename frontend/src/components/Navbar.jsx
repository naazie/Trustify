import { Link, NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navLinks = [
  { to: '/',        label: 'Dashboard' },
  { to: '/history', label: 'History'   },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/auth', { replace: true })
  }

  return (
    <header className="sticky top-0 z-50 border-b border-surface-200 bg-white/90 backdrop-blur-md shadow-sm">
      <div className="container mx-auto px-4 md:px-6 max-w-7xl">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-9 h-9 rounded-xl bg-brand-50 border border-brand-200 flex items-center justify-center shadow-sm"
            >
              <img src="/logo.png" alt="Trustify" className="w-5 h-5 object-contain" />
            </motion.div>
            <div>
              <span className="font-display text-lg font-bold text-gradient-display">Trustify</span>
              <p className="text-[10px] text-surface-400 font-medium leading-none mt-0.5 tracking-widest uppercase">Security Scanner</p>
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
                      : 'text-surface-500 hover:text-surface-800 hover:bg-surface-100'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* User area */}
          {user && (
            <div className="flex items-center gap-3">
              {/* Avatar + name */}
              <div className="flex items-center gap-2">
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name}
                    className="w-8 h-8 rounded-full border border-surface-200 object-cover"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-brand-100 border border-brand-200 flex items-center justify-center">
                    <User className="w-4 h-4 text-brand-600" />
                  </div>
                )}
                <span className="hidden sm:block text-sm font-medium text-surface-700 max-w-[120px] truncate">
                  {user.name || user.email}
                </span>
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                title="Sign out"
                className="p-2 rounded-lg text-surface-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
