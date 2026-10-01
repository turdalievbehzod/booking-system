const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

const ACCESS_KEY = 'booking.access'
const REFRESH_KEY = 'booking.refresh'

export const tokens = {
  get access() { return localStorage.getItem(ACCESS_KEY) },
  get refresh() { return localStorage.getItem(REFRESH_KEY) },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export class ApiError extends Error {
  constructor(status, data) {
    super(formatError(data) || `Request failed (${status})`)
    this.status = status
    this.data = data
  }

  // Field errors from DRF: { email: ["..."], password: ["..."] }
  fieldError(name) {
    const value = this.data?.[name]
    return Array.isArray(value) ? value.join(' ') : undefined
  }
}

function formatError(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  if (Array.isArray(data)) return data.join(' ')
  return Object.values(data).flat().join(' ')
}

let onSessionExpired = () => {}
export function setSessionExpiredHandler(fn) { onSessionExpired = fn }

// Several requests can hit 401 at once; they all wait for one refresh call.
// (Refresh tokens rotate and the old one is blacklisted, so a second refresh would fail.)
let refreshing = null

function refreshAccessToken() {
  if (!refreshing) {
    refreshing = fetch(`${API_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
      .then(async (res) => {
        if (!res.ok) return false
        tokens.set(await res.json())
        return true
      })
      .catch(() => false)
      .finally(() => { refreshing = null })
  }
  return refreshing
}

export async function api(path, { method = 'GET', body, params } = {}) {
  const url = new URL(`${API_URL}${path}`, window.location.origin)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
  })

  const send = () => fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(tokens.access ? { Authorization: `Bearer ${tokens.access}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  let res = await send()
  if (res.status === 401 && tokens.refresh) {
    if (!(await refreshAccessToken())) {
      tokens.clear()
      onSessionExpired()
    }
    // Retry with the new token, or anonymously if the session is gone
    // (public endpoints like services and slots still work).
    res = await send()
  }

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

/** Follows DRF page-number pagination and returns every item. */
export async function fetchAll(path, params = {}) {
  const items = []
  for (let page = 1; ; page += 1) {
    const data = await api(path, { params: { ...params, page } })
    items.push(...data.results)
    if (!data.next) return items
  }
}
