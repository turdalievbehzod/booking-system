import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, fetchAll } from '../../api/client'
import { Alert, EmptyState, Field, Spinner } from '../../components/ui'
import { BUSINESS_TZ, DAYS, shortTime } from '../../format'

export default function AdminHours() {
  const [params, setParams] = useSearchParams()
  const employeeId = params.get('employee') || ''
  const [employees, setEmployees] = useState(null)
  const [hours, setHours] = useState(null)
  const [form, setForm] = useState({ day_of_week: 0, start_time: '09:00', end_time: '18:00' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    fetchAll('/employees/').then((list) => {
      setEmployees(list)
      if (!employeeId && list.length) setParams({ employee: list[0].id }, { replace: true })
    }).catch((e) => setError(e.message))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const load = useCallback(() => {
    if (!employeeId) return
    setHours(null)
    fetchAll('/availabilities/', { employee: employeeId }).then(setHours).catch((e) => setError(e.message))
  }, [employeeId])

  useEffect(() => { load() }, [load])

  const add = async (days) => {
    setError('')
    setNotice('')
    // Adding several days at once: report which ones failed (e.g. overlaps) instead of stopping at the first.
    const failed = []
    for (const day of days) {
      try {
        await api('/availabilities/', {
          method: 'POST',
          body: { employee: Number(employeeId), day_of_week: day, start_time: form.start_time, end_time: form.end_time },
        })
      } catch (e) {
        failed.push(`${DAYS[day]}: ${e.message}`)
      }
    }
    if (failed.length) setError(failed.join(' '))
    else setNotice('Working hours added.')
    load()
  }

  const remove = async (item) => {
    setError('')
    try {
      await api(`/availabilities/${item.id}/`, { method: 'DELETE' })
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  if (!employees) return <Spinner />
  if (!employees.length) return <EmptyState title="No employees yet">Add an employee first.</EmptyState>

  return (
    <>
      <div className="toolbar">
        <select value={employeeId} onChange={(e) => setParams({ employee: e.target.value })} aria-label="Employee">
          {employees.map((e) => <option key={e.id} value={e.id}>{e.name}{e.is_active ? '' : ' (inactive)'}</option>)}
        </select>
        <span className="muted small">Times are in {BUSINESS_TZ}</span>
      </div>

      <Alert onClose={() => setError('')}>{error}</Alert>
      <Alert kind="success" onClose={() => setNotice('')}>{notice}</Alert>

      <div className="hours-layout">
        <div className="card week">
          {!hours && <Spinner />}
          {hours && DAYS.map((dayName, day) => {
            const items = hours.filter((h) => h.day_of_week === day)
            return (
              <div key={day} className="week-row">
                <span className="week-day">{dayName}</span>
                <div className="week-blocks">
                  {items.length === 0 && <span className="muted small">Day off</span>}
                  {items.map((h) => (
                    <span key={h.id} className="time-block">
                      {shortTime(h.start_time)}–{shortTime(h.end_time)}
                      <button type="button" aria-label="Remove" onClick={() => remove(h)}>×</button>
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <form className="card form-card" onSubmit={(e) => { e.preventDefault(); add([Number(form.day_of_week)]) }}>
          <h2>Add hours</h2>
          <Field label="Day">
            <select value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>
              {DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
            </select>
          </Field>
          <div className="form-row">
            <Field label="From">
              <input type="time" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
            </Field>
            <Field label="To">
              <input type="time" required value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
            </Field>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary">Add</button>
            <button type="button" className="btn btn-ghost" onClick={() => add([0, 1, 2, 3, 4])}>Add Mon–Fri</button>
          </div>
          <p className="muted small">Add two blocks on the same day for a lunch break, e.g. 09:00–13:00 and 14:00–18:00.</p>
        </form>
      </div>
    </>
  )
}
