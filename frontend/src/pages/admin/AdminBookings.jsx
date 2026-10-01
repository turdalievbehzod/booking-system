import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, ConfirmButton, EmptyState, Spinner, StatusBadge } from '../../components/ui'
import { formatDateTime, formatPrice, formatTime } from '../../format'

const STATUSES = ['', 'pending', 'confirmed', 'completed', 'cancelled']

function StatTile({ label, value, tone }) {
  return (
    <div className={`stat stat-${tone}`}>
      <span className="stat-value">{value ?? '–'}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

export default function AdminBookings() {
  const [filters, setFilters] = useState({ status: '', when: 'upcoming' })
  const [bookings, setBookings] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [stats, setStats] = useState({})
  const [error, setError] = useState('')

  const loadStats = useCallback(async () => {
    // `count` from the paginated response is enough; no extra stats endpoint needed.
    const count = (params) => api('/bookings/', { params: { ...params, page: 1 } }).then((d) => d.count)
    const [pending, confirmed, completed] = await Promise.all([
      count({ status: 'pending', when: 'upcoming' }),
      count({ status: 'confirmed', when: 'upcoming' }),
      count({ status: 'completed' }),
    ])
    setStats({ pending, confirmed, completed })
  }, [])

  const load = useCallback(async (pageToLoad) => {
    try {
      const data = await api('/bookings/', { params: { ...filters, page: pageToLoad } })
      setBookings((prev) => (pageToLoad === 1 ? data.results : [...(prev || []), ...data.results]))
      setTotal(data.count)
      setHasMore(Boolean(data.next))
      setPage(pageToLoad)
    } catch (e) {
      setError(e.message)
    }
  }, [filters])

  useEffect(() => {
    setBookings(null)
    load(1)
  }, [load])

  useEffect(() => { loadStats().catch(() => {}) }, [loadStats])

  const act = async (booking, action) => {
    setError('')
    try {
      const updated = await api(`/bookings/${booking.id}/${action}/`, { method: 'POST' })
      setBookings((list) => list.map((b) => (b.id === updated.id ? updated : b)))
      loadStats().catch(() => {})
    } catch (e) {
      setError(`#${booking.id}: ${e.message}`)
    }
  }

  const now = Date.now()

  return (
    <>
      <div className="stats">
        <StatTile label="Awaiting confirmation" value={stats.pending} tone="warn" />
        <StatTile label="Upcoming confirmed" value={stats.confirmed} tone="ok" />
        <StatTile label="Completed all time" value={stats.completed} tone="neutral" />
      </div>

      <div className="toolbar">
        <select value={filters.when} onChange={(e) => setFilters({ ...filters, when: e.target.value })} aria-label="Period">
          <option value="upcoming">Upcoming</option>
          <option value="past">Past</option>
          <option value="">All time</option>
        </select>
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} aria-label="Status">
          {STATUSES.map((s) => <option key={s} value={s}>{s ? s[0].toUpperCase() + s.slice(1) : 'All statuses'}</option>)}
        </select>
        <span className="muted small">{total} booking{total === 1 ? '' : 's'}</span>
      </div>

      <Alert onClose={() => setError('')}>{error}</Alert>
      {!bookings && <Spinner />}
      {bookings?.length === 0 && <EmptyState title="No bookings match these filters" />}

      {bookings?.length > 0 && (
        <div className="table-wrap card">
          <table className="table">
            <thead>
              <tr>
                <th>When</th>
                <th>Customer</th>
                <th>Service</th>
                <th>Employee</th>
                <th className="num">Price</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => {
                const started = new Date(b.start_at).getTime() <= now
                return (
                  <tr key={b.id}>
                    <td className="nowrap">
                      {formatDateTime(b.start_at)}
                      <span className="muted small"> – {formatTime(b.end_at)}</span>
                    </td>
                    <td>
                      {b.user.username}
                      <div className="muted small">{b.user.email}</div>
                    </td>
                    <td>{b.service.name}</td>
                    <td>{b.employee.name}</td>
                    <td className="num nowrap">{formatPrice(b.price)}</td>
                    <td><StatusBadge status={b.status} /></td>
                    <td className="actions">
                      {b.status === 'pending' && (
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => act(b, 'confirm')}>Confirm</button>
                      )}
                      {b.status === 'confirmed' && started && (
                        <button type="button" className="btn btn-ghost btn-sm" onClick={() => act(b, 'complete')}>Complete</button>
                      )}
                      {['pending', 'confirmed'].includes(b.status) && (
                        <ConfirmButton confirmLabel="Cancel it" onConfirm={() => act(b, 'cancel')}>Cancel</ConfirmButton>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {hasMore && (
        <div className="row-center">
          <button type="button" className="btn btn-ghost" onClick={() => load(page + 1)}>Load more</button>
        </div>
      )}
    </>
  )
}
