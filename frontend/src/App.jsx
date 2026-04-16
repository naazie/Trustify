import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import ScanDetail from './pages/ScanDetail'
import History from './pages/History'
import AuthPage from './pages/AuthPage'
import { useAuth } from './context/AuthContext'
import LoadingSpinner from './components/LoadingSpinner'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner message="Authenticating..." />
  return user ? children : <Navigate to="/auth" replace />
}

function AppContent() {
  const { pathname } = useLocation()
  const { user, loading } = useAuth()
  const isDashboard = pathname === '/'

  if (loading) return <LoadingSpinner message="Loading..." />

  // Don't show navbar on auth page
  if (pathname === '/auth') {
    return (
      <Routes>
        <Route path="/auth" element={user ? <Navigate to="/" replace /> : <AuthPage />} />
      </Routes>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className={`flex-1 ${isDashboard ? '' : 'container mx-auto px-4 md:px-8 py-10 max-w-7xl'}`}>
        <Routes>
          <Route path="/"         element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/scan/:id" element={<PrivateRoute><ScanDetail /></PrivateRoute>} />
          <Route path="/history"  element={<PrivateRoute><History /></PrivateRoute>} />
          <Route path="/auth"     element={user ? <Navigate to="/" replace /> : <AuthPage />} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t border-surface-200 bg-white/60 py-5 text-center">
        <div className="flex items-center justify-center gap-3">
          <img src="/logo.png" alt="Trustify" className="w-4 h-4 object-contain opacity-50" />
          <span className="text-xs font-medium text-surface-400 tracking-wide">
            Trustify &copy; {new Date().getFullYear()} — AI-Powered Security Orchestration
          </span>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
