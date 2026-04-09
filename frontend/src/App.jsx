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
        <main className="flex-1 container mx-auto px-4 md:px-6 py-8 max-w-7xl">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/scan/:id"    element={<ScanDetail />} />
            <Route path="/history"     element={<History />} />
            <Route path="*"            element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-white/5 py-4 text-center text-xs text-slate-600">
          Trustify &copy; {new Date().getFullYear()} — AI-Powered Security Orchestration
        </footer>
      </div>
    </BrowserRouter>
  )
}
