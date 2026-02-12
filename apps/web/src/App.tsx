
import { Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { CommandPalette } from "@/components/CommandPalette";
import ErrorBoundary from "@/components/ErrorBoundary";
import Navbar from "@/components/Navbar";
import { SkipNavigation } from "@/components/SkipNavigation";
import { Analytics, ClusterDetail, ClusterExplorer, Dashboard, Ideas } from "@/pages";

function RouteSkeleton() {
  return (
    <div className="container mx-auto py-8 space-y-4">
      <div className="h-10 w-1/3 rounded bg-muted/60 animate-pulse" />
      <div className="h-64 rounded-xl bg-muted/50 animate-pulse" />
      <div className="h-64 rounded-xl bg-muted/40 animate-pulse" />
    </div>
  );
}

function NotFound() {
  return (
    <div className="container mx-auto py-16 text-center">
      <h1 className="text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-3 text-muted-foreground">
        The page you requested does not exist.
      </p>
      <Link
        to="/"
        className="inline-flex mt-6 rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
        <SkipNavigation />
        <Navbar />
        <main id="main-content" tabIndex={-1}>
          <Suspense fallback={<RouteSkeleton />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/clusters" element={<ClusterExplorer />} />
              <Route path="/clusters/:id" element={<ClusterDetail />} />
              <Route path="/ideas" element={<Ideas />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </main>
        <CommandPalette />
      </div>
    </ErrorBoundary>
  );
}

export default App;
