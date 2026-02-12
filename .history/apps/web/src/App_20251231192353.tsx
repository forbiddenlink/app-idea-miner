import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import { LoadingSkeleton } from './pages'
import { ToastContainer, useToast } from './components/Toast'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'

// Code splitting for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ClusterExplorer = lazy(() => import('./pages/ClusterExplorer'));
const ClusterDetail = lazy(() => import('./pages/ClusterDetail'));
const Analytics = lazy(() => import('./pages/Analytics'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});

// Loading fallback for code-split routes
const PageLoader = () => (
  <div className="container mx-auto px-4 py-8">
    <LoadingSkeleton variant="page" />
  </div>
);

function App() {
  const { toasts, removeToast } = useToast();

  // Enable keyboard shortcuts
  useKeyboardShortcuts();

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <div className="min-h-screen bg-slate-900">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
              <ErrorBoundary>
                <Suspense fallback={<PageLoader />}>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/clusters" element={<ClusterExplorer />} />
                    <Route path="/clusters/:id" element={<ClusterDetail />} />
                    <Route path="/ideas" element={<div className="text-center py-20 text-slate-400">Idea Browser - Coming Soon</div>} />
                    <Route path="/analytics" element={<Analytics />} />
                  </Routes>
                </Suspense>
              </ErrorBoundary>
            </main>
            <ToastContainer toasts={toasts} onClose={removeToast} />
          </div>
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
