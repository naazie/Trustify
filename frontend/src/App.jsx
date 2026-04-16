import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import ScanDetail from './pages/ScanDetail'
import History from './pages/History'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 container mx-auto px-4 md:px-8 py-10 max-w-7xl">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/scan/:id"    element={<ScanDetail />} />
            <Route path="/history"     element={<History />} />
            <Route path="*"            element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white/50 py-5 text-center">
          <div className="flex items-center justify-center gap-3">
            <img src="/logo.png" alt="Trustify Bug" className="w-5 h-5 object-contain opacity-60" />
            <span className="text-xs font-semibold text-slate-400 tracking-wide">
              Trustify &copy; {new Date().getFullYear()} — AI-Powered Security Orchestration
            </span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}

