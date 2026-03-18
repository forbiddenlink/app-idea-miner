
import { Suspense, useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { CommandPalette } from "@/components/CommandPalette";
import ErrorBoundary from "@/components/ErrorBoundary";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import { SkipNavigation } from "@/components/SkipNavigation";
import { ToastProvider } from "@/contexts/ToastContext";
import { KeyboardShortcutsDialog } from "@/hooks/useKeyboard";
import { useKeyboardShortcuts as useAppKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { Analytics, ClusterDetail, ClusterExplorer, Dashboard, IdeaDetail, Ideas, Opportunities, Saved, Settings } from "@/pages";

function RouteSkeleton() {
  return (
    <div className="app-page">
      <div className="h-10 w-1/3 rounded-xl bg-muted/60 animate-pulse" />
      <div className="card h-64 animate-pulse bg-muted/45" />
      <div className="card h-64 animate-pulse bg-muted/40" />
    </div>
  );
}

function NotFound() {
  return (
    <div className="app-page py-16 text-center">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <p className="mt-3 text-muted-foreground">
        The page you requested does not exist.
      </p>
      <Link
        to="/"
        className="focus-ring inline-flex mt-6 rounded-xl border border-border bg-card px-4 py-2 text-sm font-semibold shadow-raised transition hover:bg-accent"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}

function App() {
  useAppKeyboardShortcuts();
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  useEffect(() => {
    const openShortcuts = () => setShortcutsOpen(true);
    globalThis.addEventListener('app:keyboard-shortcuts-open', openShortcuts as EventListener);
    return () => {
      globalThis.removeEventListener('app:keyboard-shortcuts-open', openShortcuts as EventListener);
    };
  }, []);

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="relative min-h-screen bg-background text-foreground transition-colors duration-300">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[24rem] bg-gradient-to-b from-primary/10 via-transparent to-transparent"
          />
          <SkipNavigation />
          <Navbar />
          <main id="main-content" tabIndex={-1} className="pb-8">
            <Suspense fallback={<RouteSkeleton />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/clusters" element={<ClusterExplorer />} />
                <Route path="/clusters/:id" element={<ClusterDetail />} />
                <Route path="/ideas/:id" element={<IdeaDetail />} />
                <Route path="/ideas" element={<Ideas />} />
                <Route path="/saved" element={<Saved />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </main>
          <Footer />
          <CommandPalette />
          <KeyboardShortcutsDialog isOpen={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
