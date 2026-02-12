import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import { ClusterExplorer } from './pages/ClusterExplorer'
import { ClusterDetail } from './pages/ClusterDetail'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-900">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clusters" element={<ClusterExplorer />} />
            <Route path="/clusters/:id" element={<ClusterDetail />} />
            <Route path="/ideas" element={<div className="text-center py-20 text-slate-400">Idea Browser - Coming Soon</div>} />
            <Route path="/analytics" element={<div className="text-center py-20 text-slate-400">Analytics - Coming Soon</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
