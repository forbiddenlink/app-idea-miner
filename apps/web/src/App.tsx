import { Suspense, useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { CommandPalette } from "@/components/CommandPalette";
import ErrorBoundary from "@/components/ErrorBoundary";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { SkipNavigation } from "@/components/SkipNavigation";
import { AuthProvider } from "@/contexts/AuthContext";
import { ToastProvider } from "@/contexts/ToastContext";
import { KeyboardShortcutsDialog } from "@/hooks/useKeyboard";
import { useKeyboardShortcuts as useAppKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import {
  Analytics,
  ClusterDetail,
  ClusterExplorer,
  Dashboard,
  IdeaDetail,
  Ideas,
  Opportunities,
  Saved,
  Settings,
} from "@/pages";
import Login from "@/pages/Login";

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
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="mb-6 font-display text-[6rem] font-black leading-none tracking-tight text-muted-foreground/20 select-none">
          404
        </div>
        <h1 className="text-2xl font-bold">Page not found</h1>
        <p className="mt-3 text-muted-foreground">
          The page you&rsquo;re looking for doesn&rsquo;t exist or has been
          moved.
        </p>
        <Link
          to="/"
          className="focus-ring inline-flex mt-6 rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-semibold shadow-raised transition hover:bg-accent"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

function App() {
  useAppKeyboardShortcuts();
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  useEffect(() => {
    const openShortcuts = () => setShortcutsOpen(true);
    globalThis.addEventListener(
      "app:keyboard-shortcuts-open",
      openShortcuts as EventListener,
    );
    return () => {
      globalThis.removeEventListener(
        "app:keyboard-shortcuts-open",
        openShortcuts as EventListener,
      );
    };
  }, []);

  return (
    <ErrorBoundary>
      <AuthProvider>
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
                  <Route path="/login" element={<Login />} />
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/clusters" element={<ClusterExplorer />} />
                  <Route path="/clusters/:id" element={<ClusterDetail />} />
                  <Route path="/ideas/:id" element={<IdeaDetail />} />
                  <Route path="/ideas" element={<Ideas />} />
                  <Route
                    path="/saved"
                    element={
                      <ProtectedRoute>
                        <Saved />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/opportunities" element={<Opportunities />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
            </main>
            <Footer />
            <CommandPalette />
            <KeyboardShortcutsDialog
              isOpen={shortcutsOpen}
              onClose={() => setShortcutsOpen(false)}
            />
          </div>
        </ToastProvider>{" "}
      </AuthProvider>{" "}
    </ErrorBoundary>
  );
}

export default App;
