import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { User } from './types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

interface RegisterData {
  username: string
  email: string
  display_name: string
  password: string
  invite?: string
}

const TOKEN_KEY = 'fr_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
const AuthContext = createContext<AuthContextValue | null>(null)

/** Pull a human-readable message out of FastAPI's error response. */
async function errorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg.replace(/^Value error,\s*/, '').replace(/^value is not a valid email address:\s*/, '')
    }
  } catch {
    /* ignore */
  }
  return fallback
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On load, restore the session from a saved token
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => setUser(data.user))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  const authenticate = useCallback(async (path: string, payload: object, fallback: string) => {
    const res = await fetch(`/api/auth/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(await errorMessage(res, fallback))
    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.token)
    setUser(data.user)
  }, [])

  const login = useCallback(
    (username: string, password: string) =>
      authenticate('login', { username, password }, 'Could not log in.'),
    [authenticate],
  )

  const register = useCallback(
    (data: RegisterData) => authenticate('register', data, 'Could not create account.'),
    [authenticate],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
