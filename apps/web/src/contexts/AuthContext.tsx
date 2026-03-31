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

const API_BASE_URL = import.meta.env.VITE_API_URL || "";
const TOKEN_KEY = "aim_auth_token";

interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY),
  );
  const [isLoading, setIsLoading] = useState(!!token);

  // Fetch /me whenever we have a token
  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    axios
      .get<AuthUser>(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setUser(res.data))
      .catch(() => {
        // Token is invalid or expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await axios.post<{ access_token: string }>(
      `${API_BASE_URL}/api/v1/auth/login`,
      { email, password },
    );
    const newToken = res.data.access_token;
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const res = await axios.post<{ access_token: string }>(
      `${API_BASE_URL}/api/v1/auth/register`,
      { email, password },
    );
    const newToken = res.data.access_token;
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, token, isLoading, login, register, logout }),
    [user, token, isLoading, login, register, logout],
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
