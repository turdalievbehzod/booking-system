import { useState } from 'react'

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="spinner-wrap" role="status">
      <span className="spinner" />
      <span className="muted">{label}</span>
    </div>
  )
}

export function Alert({ kind = 'error', children, onClose }) {
  if (!children) return null
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
      {onClose && (
        <button type="button" className="alert-close" onClick={onClose} aria-label="Dismiss">×</button>
      )}
    </div>
  )
}

const STATUS_LABELS = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
  completed: 'Completed',
}

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status] || status}</span>
}

export function EmptyState({ title, children }) {
  return (
    <div className="empty">
      <p className="empty-title">{title}</p>
      {children && <div className="muted">{children}</div>}
    </div>
  )
}

/**
 * Two-step button for destructive actions: the first click asks, the second one acts.
 * Keeps the confirmation inline instead of using window.confirm().
 */
export function ConfirmButton({ children, confirmLabel = 'Sure?', onConfirm, className = 'btn btn-danger-ghost btn-sm', disabled }) {
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)

  if (!asking) {
    return (
      <button type="button" className={className} disabled={disabled} onClick={() => setAsking(true)}>
        {children}
      </button>
    )
  }
  return (
    <span className="confirm-inline">
      <button
        type="button"
        className="btn btn-danger btn-sm"
        disabled={busy}
        onClick={async () => {
          setBusy(true)
          try {
            await onConfirm()
          } finally {
            setBusy(false)
            setAsking(false)
          }
        }}
      >
        {busy ? '…' : confirmLabel}
      </button>
      <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => setAsking(false)}>
        No
      </button>
    </span>
  )
}

export function Field({ label, error, hint, children }) {
  return (
    <label className={`field ${error ? 'field-invalid' : ''}`}>
      <span className="field-label">{label}</span>
      {children}
      {error ? <span className="field-error">{error}</span> : hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}
