import axios from "axios";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { apiClient } from "@/services/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  /**
   * Whether a session is currently active. The access token itself lives in
   * an httpOnly cookie the browser manages — JavaScript never sees its
   * value, so there is no `token` field to read here. Session state is
   * derived from whether GET /api/v1/auth/me succeeded.
   */
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.get<AuthUser>(`${API_BASE_URL}/api/v1/auth/me`, {
        withCredentials: true,
      });
      setUser(res.data);
    } catch {
      // No session cookie, or it's invalid/expired.
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      // The server sets the session cookie via Set-Cookie on this response;
      // withCredentials is what makes the browser store it.
      await axios.post(
        `${API_BASE_URL}/api/v1/auth/login`,
        { email, password },
        { withCredentials: true },
      );
      await fetchCurrentUser();
    },
    [fetchCurrentUser],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      await axios.post(
        `${API_BASE_URL}/api/v1/auth/register`,
        { email, password },
        { withCredentials: true },
      );
      await fetchCurrentUser();
    },
    [fetchCurrentUser],
  );

  const logout = useCallback(async () => {
    // apiClient (not plain axios) so the CSRF header interceptor fires —
    // logout is a state-changing POST behind the same CSRF check as any
    // other mutating request.
    try {
      await apiClient.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
