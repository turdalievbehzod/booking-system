import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Alert, ConfirmButton, EmptyState, Spinner, StatusBadge } from '../components/ui'
import { formatDateTime, formatPrice, formatTime } from '../format'

const TABS = [
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'past', label: 'Past' },
]

export default function MyBookingsPage() {
  const [tab, setTab] = useState('upcoming')
  const [bookings, setBookings] = useState(null)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async (pageToLoad) => {
    try {
      const data = await api('/bookings/', { params: { when: tab, page: pageToLoad } })
      setBookings((prev) => (pageToLoad === 1 ? data.results : [...(prev || []), ...data.results]))
      setHasMore(Boolean(data.next))
      setPage(pageToLoad)
    } catch (e) {
      setError(e.message)
    }
  }, [tab])

  useEffect(() => {
    setBookings(null)
    load(1)
  }, [load])

  const cancel = async (booking) => {
    setError('')
    try {
      const updated = await api(`/bookings/${booking.id}/cancel/`, { method: 'POST' })
      setBookings((list) => list.map((b) => (b.id === updated.id ? updated : b)))
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>My bookings</h1>
        <Link to="/" className="btn btn-primary">New booking</Link>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className={`tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Alert onClose={() => setError('')}>{error}</Alert>
      {!bookings && <Spinner />}
      {bookings?.length === 0 && (
        <EmptyState title={tab === 'upcoming' ? 'No upcoming bookings' : 'No past bookings'}>
          {tab === 'upcoming' && <Link to="/">Book a service</Link>}
        </EmptyState>
      )}

      <div className="booking-list">
        {bookings?.map((b) => (
          <article key={b.id} className="card booking-card">
            <div className="booking-when">
              <span className="booking-date">{formatDateTime(b.start_at)}</span>
              <span className="muted small">until {formatTime(b.end_at)}</span>
            </div>
            <div className="booking-what">
              <strong>{b.service.name}</strong>
              <span className="muted">with {b.employee.name}</span>
            </div>
            <div className="booking-side">
              <span className="price">{formatPrice(b.price)}</span>
              <StatusBadge status={b.status} />
              {tab === 'upcoming' && ['pending', 'confirmed'].includes(b.status) && (
                <ConfirmButton confirmLabel="Cancel booking" onConfirm={() => cancel(b)}>Cancel</ConfirmButton>
              )}
            </div>
          </article>
        ))}
      </div>

      {hasMore && (
        <div className="row-center">
          <button type="button" className="btn btn-ghost" onClick={() => load(page + 1)}>Load more</button>
        </div>
      )}
    </>
  )
}
