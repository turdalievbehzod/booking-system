import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchAll } from '../api/client'
import { Alert, EmptyState, Spinner } from '../components/ui'
import { BUSINESS_NAME, formatDuration, formatPrice } from '../format'

export default function ServicesPage() {
  const [services, setServices] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAll('/services/')
      // Admins get inactive services from the API too; customers never see them here.
      .then((items) => setServices(items.filter((s) => s.is_active)))
      .catch((e) => setError(e.message))
  }, [])

  return (
    <>
      <section className="hero">
        <h1>Book your appointment at {BUSINESS_NAME}</h1>
        <p className="muted">Choose a service, pick a time that suits you, and you're done.</p>
      </section>

      <Alert>{error}</Alert>
      {!services && !error && <Spinner />}
      {services && services.length === 0 && (
        <EmptyState title="No services yet">Please check back later.</EmptyState>
      )}

      <div className="service-grid">
        {services?.map((service) => (
          <article key={service.id} className="card service-card">
            <div className="service-card-body">
              <h2>{service.name}</h2>
              {service.description && <p className="muted">{service.description}</p>}
              <div className="service-meta">
                <span className="chip">{formatDuration(service.duration_minutes)}</span>
                {service.employees.length > 0 && (
                  <span className="muted small">
                    with {service.employees.map((e) => e.name).join(', ')}
                  </span>
                )}
              </div>
            </div>
            <div className="service-card-footer">
              <span className="price">{formatPrice(service.price)}</span>
              {service.employees.length > 0 ? (
                <Link to={`/services/${service.id}/book`} className="btn btn-primary">Book</Link>
              ) : (
                <span className="muted small">Not available</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </>
  )
}
