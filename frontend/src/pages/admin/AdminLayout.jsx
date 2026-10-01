import { NavLink, Outlet } from 'react-router-dom'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default function AdminLayout() {
  return (
    <>
      <div className="page-head">
        <h1>Admin</h1>
        {/* /admin in this app is the React admin; Django's admin lives on the backend. */}
        <a href={`${BACKEND_URL}/admin/`} className="muted small" target="_blank" rel="noreferrer">Django admin ↗</a>
      </div>
      <nav className="tabs">
        <NavLink to="/admin" end className="tab">Bookings</NavLink>
        <NavLink to="/admin/services" className="tab">Services</NavLink>
        <NavLink to="/admin/employees" className="tab">Employees</NavLink>
        <NavLink to="/admin/hours" className="tab">Working hours</NavLink>
      </nav>
      <Outlet />
    </>
  )
}
