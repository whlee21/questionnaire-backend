import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import { ProtectedRoute } from '../components/ProtectedRoute'
import LoginPage from '../pages/LoginPage'
import DashboardPage from '../pages/DashboardPage'

describe('App routing', () => {
  beforeEach(() => {
    localStorage.removeItem('pushnotify_token')
  })

  it('redirects unauthenticated user from /compose to /login', () => {
    render(
      <MemoryRouter initialEntries={['/compose']}>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/compose" element={<DashboardPage />} />
              </Route>
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: /pushnotify/i })).toBeInTheDocument()
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument()
  })

  it('renders protected content when token is present', () => {
    localStorage.setItem('pushnotify_token', 'fake-jwt-token')
    render(
      <MemoryRouter initialEntries={['/compose']}>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/compose" element={<DashboardPage />} />
              </Route>
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    )
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument()
  })
})
