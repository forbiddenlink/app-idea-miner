import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import { ToastContainer, useToast } from './components/Toast'
import { SkipNavigation } from './components/SkipNavigation'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'

// Code splitting for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ClusterExplorer = lazy(() => import('./pages/ClusterExplorer'));
const ClusterDetail = lazy(() => import('./pages/ClusterDetail'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Ideas = lazy(() => import('./pages/Ideas'));

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
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-slate-700 rounded w-1/3"></div>
      <div className="h-4 bg-slate-700 rounded w-1/2"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-48 bg-slate-800 rounded-lg"></div>
        ))}
      </div>
    </div>
  </div>
);

// AppContent component that sits inside Router context
interface AppContentProps {
  toasts: Array<{ id: string; message: string; type: string }>;
  onRemoveToast: (id: string) => void;
}

function AppContent({ toasts, onRemoveToast }: AppContentProps) {
  // Enable keyboard shortcuts (now inside Router context)
  useKeyboardShortcuts();

  return (
    <div className="min-h-screen bg-slate-900">
      <SkipNavigation />
      <Navbar />
      <main id="main-content" className="container mx-auto px-4 py-8" role="main" aria-label="Main content">
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
      <ToastContainer toasts={toasts} onClose={onRemoveToast} />
    </div>
  );
}

function App() {
  const { toasts, removeToast } = useToast();

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <AppContent toasts={toasts} onRemoveToast={removeToast} />
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
