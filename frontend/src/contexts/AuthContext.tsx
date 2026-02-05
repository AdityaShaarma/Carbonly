import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { Company, User } from "@/types/api";
import { fetchMe } from "@/api/auth";
import { getStoredToken } from "@/api/client";

interface AuthState {
  user: User | null;
  company: Company | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<
  (AuthState & { refetchMe: () => Promise<void>; clearAuth: () => void }) | null
>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetchMe = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setCompany(null);
      setIsLoading(false);
      return;
    }
    try {
      const data = await fetchMe();
      setUser(data.user);
      setCompany(data.company);
    } catch {
      setUser(null);
      setCompany(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    refetchMe();
  }, [refetchMe]);

  const clearAuth = useCallback(() => {
    setUser(null);
    setCompany(null);
    setIsLoading(false);
  }, []);

  const value: AuthState & {
    refetchMe: () => Promise<void>;
    clearAuth: () => void;
  } = {
    user,
    company,
    isLoading,
    isAuthenticated: !!user && !!company,
    refetchMe,
    clearAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
