// All times are shown in the business timezone (same as Django's TIME_ZONE),
// so a customer abroad sees the time at which they must actually show up.
export const BUSINESS_TZ = import.meta.env.VITE_BUSINESS_TZ || 'Asia/Tashkent'
export const BUSINESS_NAME = import.meta.env.VITE_BUSINESS_NAME || 'Studio Booking'
const CURRENCY = import.meta.env.VITE_CURRENCY || 'UZS'

export const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

/** Today's date in the business timezone, as YYYY-MM-DD. */
export function todayISO() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: BUSINESS_TZ, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}

/** Adds days to a YYYY-MM-DD string (calendar math, no timezone involved). */
export function addDays(isoDate, days) {
  const d = new Date(`${isoDate}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/** Parts of a YYYY-MM-DD date for the date picker. */
export function dateParts(isoDate) {
  const d = new Date(`${isoDate}T12:00:00Z`)
  const fmt = (opts) => new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', ...opts }).format(d)
  return { weekday: fmt({ weekday: 'short' }), day: fmt({ day: 'numeric' }), month: fmt({ month: 'short' }) }
}

export function formatLongDate(isoDate) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long',
  }).format(new Date(`${isoDate}T12:00:00Z`))
}

export function formatTime(dateTime) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: BUSINESS_TZ, hour: '2-digit', minute: '2-digit',
  }).format(new Date(dateTime))
}

export function formatDateTime(dateTime) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: BUSINESS_TZ, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  }).format(new Date(dateTime))
}

export function formatPrice(value) {
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value))} ${CURRENCY}`
}

export function formatDuration(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (!h) return `${m} min`
  return m ? `${h} h ${m} min` : `${h} h`
}

/** "09:00:00" -> "09:00" */
export function shortTime(time) {
  return time.slice(0, 5)
}
