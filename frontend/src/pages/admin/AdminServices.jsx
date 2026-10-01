import { useEffect, useState } from 'react'
import { api, fetchAll } from '../../api/client'
import { Alert, ConfirmButton, EmptyState, Field, Spinner } from '../../components/ui'
import { formatDuration, formatPrice } from '../../format'

const EMPTY = { name: '', description: '', duration_minutes: 30, price: '', is_active: true }

export default function AdminServices() {
  const [services, setServices] = useState(null)
  const [editing, setEditing] = useState(null) // null = closed, {} = new, service = edit
  const [form, setForm] = useState(EMPTY)
  const [formError, setFormError] = useState(null)
  const [error, setError] = useState('')

  const load = () => fetchAll('/services/').then(setServices).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  const open = (service) => {
    setEditing(service || {})
    setForm(service ? { ...EMPTY, ...service } : EMPTY)
    setFormError(null)
  }

  const save = async (e) => {
    e.preventDefault()
    setFormError(null)
    const body = {
      name: form.name,
      description: form.description,
      duration_minutes: Number(form.duration_minutes),
      price: form.price,
      is_active: form.is_active,
    }
    try {
      if (editing.id) await api(`/services/${editing.id}/`, { method: 'PATCH', body })
      else await api('/services/', { method: 'POST', body })
      setEditing(null)
      load()
    } catch (err) {
      setFormError(err)
    }
  }

  const setActive = async (service, active) => {
    setError('')
    try {
      // DELETE is a soft delete on the backend (is_active=false).
      if (active) await api(`/services/${service.id}/`, { method: 'PATCH', body: { is_active: true } })
      else await api(`/services/${service.id}/`, { method: 'DELETE' })
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  const fe = (name) => formError?.fieldError?.(name)

  return (
    <>
      <div className="toolbar">
        <button type="button" className="btn btn-primary" onClick={() => open(null)}>+ New service</button>
      </div>
      <Alert onClose={() => setError('')}>{error}</Alert>

      {editing && (
        <form className="card form-card" onSubmit={save}>
          <h2>{editing.id ? `Edit “${editing.name}”` : 'New service'}</h2>
          {formError && !['name', 'duration_minutes', 'price'].some(fe) && <Alert>{formError.message}</Alert>}
          <div className="form-row">
            <Field label="Name" error={fe('name')}>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
            <Field label="Duration (minutes)" error={fe('duration_minutes')} hint="5 – 480">
              <input type="number" min="5" max="480" step="5" required value={form.duration_minutes}
                onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} />
            </Field>
            <Field label="Price" error={fe('price')}>
              <input type="number" min="0" step="0.01" required value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })} />
            </Field>
          </div>
          <Field label="Description" error={fe('description')}>
            <textarea rows="2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <label className="checkbox">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Active (bookable by customers)
          </label>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary">Save</button>
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </form>
      )}

      {!services && <Spinner />}
      {services?.length === 0 && <EmptyState title="No services yet">Create the first one above.</EmptyState>}
      {services?.length > 0 && (
        <div className="table-wrap card">
          <table className="table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Duration</th>
                <th className="num">Price</th>
                <th>Employees</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {services.map((s) => (
                <tr key={s.id} className={s.is_active ? '' : 'row-muted'}>
                  <td>
                    <strong>{s.name}</strong>
                    {s.description && <div className="muted small">{s.description}</div>}
                  </td>
                  <td className="nowrap">{formatDuration(s.duration_minutes)}</td>
                  <td className="num nowrap">{formatPrice(s.price)}</td>
                  <td>{s.employees.map((e) => e.name).join(', ') || <span className="muted">None</span>}</td>
                  <td>{s.is_active ? <span className="badge badge-confirmed">Active</span> : <span className="badge badge-cancelled">Inactive</span>}</td>
                  <td className="actions">
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => open(s)}>Edit</button>
                    {s.is_active ? (
                      <ConfirmButton confirmLabel="Deactivate" onConfirm={() => setActive(s, false)}>Deactivate</ConfirmButton>
                    ) : (
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setActive(s, true)}>Activate</button>
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
