import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Alert, Field } from '../components/ui'
import { safeNext } from './LoginPage'

const EMPTY = { username: '', email: '', first_name: '', last_name: '', password: '' }

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await register(form)
      navigate(next, { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  const fieldError = (name) => error?.fieldError?.(name)
  const hasFieldErrors = Object.keys(EMPTY).some(fieldError)

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Create account</h1>
        {error && !hasFieldErrors && <Alert>{error.message}</Alert>}
        <div className="form-row">
          <Field label="First name" error={fieldError('first_name')}>
            <input autoComplete="given-name" value={form.first_name} onChange={set('first_name')} />
          </Field>
          <Field label="Last name" error={fieldError('last_name')}>
            <input autoComplete="family-name" value={form.last_name} onChange={set('last_name')} />
          </Field>
        </div>
        <Field label="Username" error={fieldError('username')}>
          <input autoComplete="username" required value={form.username} onChange={set('username')} />
        </Field>
        <Field label="Email" error={fieldError('email')} hint="Booking confirmations are sent here.">
          <input type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        </Field>
        <Field label="Password" error={fieldError('password') || fieldError('non_field_errors')} hint="At least 8 characters, not too common.">
          <input type="password" autoComplete="new-password" required value={form.password} onChange={set('password')} />
        </Field>
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Creating account…' : 'Sign up'}
        </button>
        <p className="muted small center">
          Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Log in</Link>
        </p>
      </form>
    </div>
  )
}
