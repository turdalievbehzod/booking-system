import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, fetchAll } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, Spinner } from '../components/ui'
import {
  addDays, dateParts, formatDuration, formatLongDate, formatPrice, formatTime, todayISO,
} from '../format'

const DAYS_VISIBLE = 7
const HORIZON_DAYS = 60 // same as BOOKING_HORIZON_DAYS in Django settings

export default function BookPage() {
  const { serviceId } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [service, setService] = useState(null)
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('') // '' = any employee
  const today = todayISO()
  const [weekStart, setWeekStart] = useState(today)
  const [date, setDate] = useState(today)
  const [slots, setSlots] = useState(null)
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [booking, setBooking] = useState(false)
  const [booked, setBooked] = useState(null)

  useEffect(() => {
    Promise.all([
      api(`/services/${serviceId}/`),
      fetchAll('/employees/', { service_id: serviceId }),
    ])
      .then(([s, e]) => { setService(s); setEmployees(e) })
      .catch((e) => setError(e.status === 404 ? 'This service is not available.' : e.message))
  }, [serviceId])

  const loadSlots = useCallback(async () => {
    setSlots(null)
    setSelected(null)
    try {
      setSlots(await api('/slots/', { params: { service_id: serviceId, date, employee_id: employeeId } }))
    } catch (e) {
      setError(e.message)
      setSlots([])
    }
  }, [serviceId, date, employeeId])

  useEffect(() => { loadSlots() }, [loadSlots])

  // With "any employee", several employees can be free at the same time:
  // show each time once and book the first free employee.
  const times = useMemo(() => {
    const byStart = new Map()
    slots?.forEach((slot) => { if (!byStart.has(slot.start_at)) byStart.set(slot.start_at, slot) })
    return [...byStart.values()]
  }, [slots])

  const groups = useMemo(() => {
    const hour = (slot) => Number(formatTime(slot.start_at).slice(0, 2))
    return [
      { label: 'Morning', items: times.filter((s) => hour(s) < 12) },
      { label: 'Afternoon', items: times.filter((s) => hour(s) >= 12 && hour(s) < 17) },
      { label: 'Evening', items: times.filter((s) => hour(s) >= 17) },
    ].filter((g) => g.items.length)
  }, [times])

  const days = Array.from({ length: DAYS_VISIBLE }, (_, i) => addDays(weekStart, i))
  const lastDay = addDays(today, HORIZON_DAYS)

  const book = async () => {
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`)
      return
    }
    setBooking(true)
    setError('')
    try {
      setBooked(await api('/bookings/', {
        method: 'POST',
        body: { service_id: Number(serviceId), employee_id: selected.employee_id, start_at: selected.start_at },
      }))
    } catch (e) {
      setError(e.status === 409 ? 'Sorry, someone just booked this time. Please pick another one.' : e.message)
      if (e.status === 409) loadSlots()
    } finally {
      setBooking(false)
    }
  }

  if (booked) {
    return (
      <div className="card success-card">
        <div className="success-icon" aria-hidden="true">✓</div>
        <h1>Booking received</h1>
        <p className="muted">
          {booked.service.name} with {booked.employee.name}<br />
          {formatLongDate(date)}, {formatTime(booked.start_at)}–{formatTime(booked.end_at)}
        </p>
        <p>Your booking is <strong>pending</strong> until the studio confirms it. We've sent you an email.</p>
        <div className="row-center">
          <Link to="/bookings" className="btn btn-primary">My bookings</Link>
          <Link to="/" className="btn btn-ghost">Book another service</Link>
        </div>
      </div>
    )
  }

  if (!service) return error ? <Alert>{error}</Alert> : <Spinner />

  return (
    <div className="book-layout">
      <div className="book-main">
        <Link to="/" className="back-link">← All services</Link>
        <h1>{service.name}</h1>
        <p className="muted">
          {formatDuration(service.duration_minutes)} · {formatPrice(service.price)}
          {service.description && <> · {service.description}</>}
        </p>

        <section className="step">
          <h2 className="step-title"><span className="step-num">1</span> Specialist</h2>
          <div className="pill-row">
            <button type="button" className={`pill ${employeeId === '' ? 'active' : ''}`} onClick={() => setEmployeeId('')}>
              Anyone available
            </button>
            {employees.map((e) => (
              <button
                key={e.id}
                type="button"
                className={`pill ${employeeId === e.id ? 'active' : ''}`}
                onClick={() => setEmployeeId(e.id)}
              >
                {e.name}
              </button>
            ))}
          </div>
        </section>

        <section className="step">
          <h2 className="step-title"><span className="step-num">2</span> Date</h2>
          <div className="date-strip">
            <button
              type="button"
              className="btn btn-ghost btn-icon"
              aria-label="Previous week"
              disabled={weekStart <= today}
              onClick={() => setWeekStart(addDays(weekStart, -DAYS_VISIBLE) < today ? today : addDays(weekStart, -DAYS_VISIBLE))}
            >
              ‹
            </button>
            <div className="date-days">
              {days.map((d) => {
                const p = dateParts(d)
                return (
                  <button
                    key={d}
                    type="button"
                    className={`date-day ${d === date ? 'active' : ''}`}
                    disabled={d > lastDay}
                    onClick={() => setDate(d)}
                  >
                    <span className="date-weekday">{d === today ? 'Today' : p.weekday}</span>
                    <span className="date-num">{p.day}</span>
                    <span className="date-month">{p.month}</span>
                  </button>
                )
              })}
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-icon"
              aria-label="Next week"
              disabled={addDays(weekStart, DAYS_VISIBLE) > lastDay}
              onClick={() => setWeekStart(addDays(weekStart, DAYS_VISIBLE))}
            >
              ›
            </button>
          </div>
        </section>

        <section className="step">
          <h2 className="step-title"><span className="step-num">3</span> Time</h2>
          {!slots && <Spinner label="Finding free times…" />}
          {slots && times.length === 0 && (
            <EmptyState title="No free times on this day">Try another date or specialist.</EmptyState>
          )}
          {groups.map((group) => (
            <div key={group.label} className="slot-group">
              <div className="slot-group-label">{group.label}</div>
              <div className="slot-grid">
                {group.items.map((slot) => (
                  <button
                    key={slot.start_at}
                    type="button"
                    className={`slot ${selected?.start_at === slot.start_at ? 'active' : ''}`}
                    onClick={() => setSelected(slot)}
                  >
                    {formatTime(slot.start_at)}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>

      <aside className="card summary">
        <h2>Summary</h2>
        <dl className="summary-list">
          <dt>Service</dt><dd>{service.name}</dd>
          <dt>Specialist</dt>
          <dd>{selected ? selected.employee_name : employees.find((e) => e.id === employeeId)?.name || 'Anyone available'}</dd>
          <dt>Date</dt><dd>{formatLongDate(date)}</dd>
          <dt>Time</dt>
          <dd>{selected ? `${formatTime(selected.start_at)}–${formatTime(selected.end_at)}` : '—'}</dd>
        </dl>
        <div className="summary-total">
          <span>Total</span>
          <span className="price">{formatPrice(service.price)}</span>
        </div>
        <Alert onClose={() => setError('')}>{error}</Alert>
        <button type="button" className="btn btn-primary btn-block" disabled={!selected || booking} onClick={book}>
          {booking ? 'Booking…' : user ? 'Confirm booking' : 'Log in to book'}
        </button>
        <p className="muted small">Free cancellation up to 2 hours before your appointment.</p>
      </aside>
    </div>
  )
}
