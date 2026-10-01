import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, setSessionExpiredHandler, tokens } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokens.access))

  const loadMe = useCallback(async () => {
    try {
      setUser(await api('/auth/me/'))
    } catch {
      tokens.clear()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    if (tokens.access) loadMe()
  }, [loadMe])

  const login = useCallback(async (username, password) => {
    tokens.set(await api('/auth/login/', { method: 'POST', body: { username, password } }))
    await loadMe()
  }, [loadMe])

  const register = useCallback(async (data) => {
    await api('/auth/register/', { method: 'POST', body: data })
    await login(data.username, data.password)
  }, [login])

  const logout = useCallback(async () => {
    try {
      if (tokens.refresh) await api('/auth/logout/', { method: 'POST', body: { refresh: tokens.refresh } })
    } catch {
      // Token already invalid: nothing to blacklist.
    }
    tokens.clear()
    setUser(null)
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    isAdmin: user?.role === 'admin',
    login,
    register,
    logout,
  }), [user, loading, login, register, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
