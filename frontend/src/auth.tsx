import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, ApiError, type User } from './api';

type AuthState = {
  user: User | null; loading: boolean; error: string;
  setUser: (user: User | null) => void; reload: () => Promise<void>;
  signOut: () => Promise<void>;
};
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function reload() {
    setError('');
    try { setUser(await api<User>('/auth/me/')); }
    catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) setUser(null);
      else setError(e instanceof Error ? e.message : 'No se pudo conectar.');
    } finally { setLoading(false); }
  }
  useEffect(() => {
    void reload();
    const check = () => { void reload(); };
    window.addEventListener('session-check', check);
    return () => window.removeEventListener('session-check', check);
  }, []);
  useEffect(() => {
    if (user) void api<{ date_format: string }>('/settings/').then(s => localStorage.setItem('date-format', s.date_format)).catch(() => undefined);
  }, [user?.id]);
  async function signOut() {
    await api('/auth/logout/', 'POST');
    setUser(null);
  }
  return <AuthContext.Provider value={{ user, loading, error, setUser, reload, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('AuthProvider requerido');
  return context;
}
