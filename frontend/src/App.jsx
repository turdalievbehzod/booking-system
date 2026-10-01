import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import BookPage from './pages/BookPage'
import LoginPage from './pages/LoginPage'
import MyBookingsPage from './pages/MyBookingsPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'
import ServicesPage from './pages/ServicesPage'
import AdminBookings from './pages/admin/AdminBookings'
import AdminEmployees from './pages/admin/AdminEmployees'
import AdminHours from './pages/admin/AdminHours'
import AdminLayout from './pages/admin/AdminLayout'
import AdminServices from './pages/admin/AdminServices'

function RequireAuth({ admin = false, children }) {
  const { user, loading, isAdmin } = useAuth()
  const location = useLocation()
  if (loading) return <Spinner />
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />
  if (admin && !isAdmin) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ServicesPage />} />
        <Route path="services/:serviceId/book" element={<BookPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="bookings" element={<RequireAuth><MyBookingsPage /></RequireAuth>} />
        <Route path="admin" element={<RequireAuth admin><AdminLayout /></RequireAuth>}>
          <Route index element={<AdminBookings />} />
          <Route path="services" element={<AdminServices />} />
          <Route path="employees" element={<AdminEmployees />} />
          <Route path="hours" element={<AdminHours />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
