import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/contexts/AuthContext";

/**
 * Wraps a route and redirects unauthenticated users to /login.
 * Preserves the original destination in `state.from` for post-login redirect.
 */
export default function ProtectedRoute({
  children,
}: Readonly<{ children: ReactNode }>) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
