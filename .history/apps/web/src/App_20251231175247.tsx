import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import { ClusterExplorer } from './pages/ClusterExplorer'
import { ClusterDetail } from './pages/ClusterDetail'
import { Analytics } from './pages/Analytics'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-slate-900">
          <Navbar />
          <main className="container mx-auto px-4 py-8">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/clusters" element={<ClusterExplorer />} />
                <Route path="/clusters/:id" element={<ClusterDetail />} />
                <Route path="/ideas" element={<div className="text-center py-20 text-slate-400">Idea Browser - Coming Soon</div>} />
                <Route path="/analytics" element={<Analytics />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </Router>
    </ErrorBoundary>
  )
}

export default App
