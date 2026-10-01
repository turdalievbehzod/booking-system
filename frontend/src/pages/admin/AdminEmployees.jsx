import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fetchAll } from '../../api/client'
import { Alert, ConfirmButton, EmptyState, Field, Spinner } from '../../components/ui'

const EMPTY = { name: '', email: '', is_active: true, service_ids: [] }

export default function AdminEmployees() {
  const [employees, setEmployees] = useState(null)
  const [services, setServices] = useState([])
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [formError, setFormError] = useState(null)
  const [error, setError] = useState('')

  const load = () => fetchAll('/employees/').then(setEmployees).catch((e) => setError(e.message))
  useEffect(() => {
    load()
    fetchAll('/services/').then(setServices).catch(() => {})
  }, [])

  const serviceName = (id) => services.find((s) => s.id === id)?.name || `#${id}`

  const open = (employee) => {
    setEditing(employee || {})
    setForm(employee ? { ...EMPTY, ...employee } : EMPTY)
    setFormError(null)
  }

  const toggleService = (id) => setForm((f) => ({
    ...f,
    service_ids: f.service_ids.includes(id) ? f.service_ids.filter((x) => x !== id) : [...f.service_ids, id],
  }))

  const save = async (e) => {
    e.preventDefault()
    setFormError(null)
    const body = { name: form.name, email: form.email, is_active: form.is_active, service_ids: form.service_ids }
    try {
      if (editing.id) await api(`/employees/${editing.id}/`, { method: 'PATCH', body })
      else await api('/employees/', { method: 'POST', body })
      setEditing(null)
      load()
    } catch (err) {
      setFormError(err)
    }
  }

  const setActive = async (employee, active) => {
    setError('')
    try {
      if (active) await api(`/employees/${employee.id}/`, { method: 'PATCH', body: { is_active: true } })
      else await api(`/employees/${employee.id}/`, { method: 'DELETE' })
      load()
    } catch (e) {
      // 409: the employee still has upcoming bookings.
      setError(`${employee.name}: ${e.message}`)
    }
  }

  const fe = (name) => formError?.fieldError?.(name)

  return (
    <>
      <div className="toolbar">
        <button type="button" className="btn btn-primary" onClick={() => open(null)}>+ New employee</button>
      </div>
      <Alert onClose={() => setError('')}>{error}</Alert>

      {editing && (
        <form className="card form-card" onSubmit={save}>
          <h2>{editing.id ? `Edit ${editing.name}` : 'New employee'}</h2>
          {formError && !['name', 'email'].some(fe) && <Alert>{formError.message}</Alert>}
          <div className="form-row">
            <Field label="Name" error={fe('name')}>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
            <Field label="Email" error={fe('email')}>
              <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </Field>
          </div>
          <fieldset className="fieldset">
            <legend className="field-label">Services this employee provides</legend>
            {services.length === 0 && <span className="muted small">Create services first.</span>}
            <div className="check-grid">
              {services.map((s) => (
                <label key={s.id} className="checkbox">
                  <input type="checkbox" checked={form.service_ids.includes(s.id)} onChange={() => toggleService(s.id)} />
                  {s.name}{!s.is_active && <span className="muted small"> (inactive)</span>}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="checkbox">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Active (can be booked)
          </label>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary">Save</button>
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </form>
      )}

      {!employees && <Spinner />}
      {employees?.length === 0 && <EmptyState title="No employees yet">Add the first one above.</EmptyState>}
      {employees?.length > 0 && (
        <div className="table-wrap card">
          <table className="table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Services</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id} className={emp.is_active ? '' : 'row-muted'}>
                  <td>
                    <strong>{emp.name}</strong>
                    <div className="muted small">{emp.email}</div>
                  </td>
                  <td>{emp.service_ids.map(serviceName).join(', ') || <span className="muted">None</span>}</td>
                  <td>{emp.is_active ? <span className="badge badge-confirmed">Active</span> : <span className="badge badge-cancelled">Inactive</span>}</td>
                  <td className="actions">
                    <Link to={`/admin/hours?employee=${emp.id}`} className="btn btn-ghost btn-sm">Hours</Link>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => open(emp)}>Edit</button>
                    {emp.is_active ? (
                      <ConfirmButton confirmLabel="Deactivate" onConfirm={() => setActive(emp, false)}>Deactivate</ConfirmButton>
                    ) : (
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setActive(emp, true)}>Activate</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
