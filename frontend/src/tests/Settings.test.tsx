import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import SettingsPage from '../pages/SettingsPage'

vi.mock('../api/client', () => ({
  apiClient: { post: vi.fn(), get: vi.fn(), delete: vi.fn(), put: vi.fn() },
}))

import { apiClient } from '../api/client'

function renderSettings() {
  localStorage.setItem('pushnotify_token', 'test-token')
  return render(
    <MemoryRouter initialEntries={['/settings']}>
      <AuthProvider>
        <ToastProvider>
          <Routes><Route path="/settings" element={<SettingsPage />} /></Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('SettingsPage', () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.setItem('pushnotify_token', 'test-token') })

  it('renders heading and level select', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ level: 'INFO' })
    renderSettings()
    expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByLabelText(/new level/i)).toBeInTheDocument()
    })
  })

  it('displays current level from API', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ level: 'WARNING' })
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText('WARNING')).toBeInTheDocument()
    })
  })

  it('calls PUT with selected level on Apply', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ level: 'INFO' })
    vi.mocked(apiClient.put).mockResolvedValueOnce({ level: 'DEBUG' })
    renderSettings()
    await waitFor(() => expect(screen.getByLabelText(/new level/i)).toBeInTheDocument())

    fireEvent.change(screen.getByLabelText(/new level/i), { target: { value: 'DEBUG' } })
    fireEvent.click(screen.getByRole('button', { name: /apply/i }))

    await waitFor(() => {
      expect(apiClient.put).toHaveBeenCalledWith(
        '/api/v1/admin/log-level',
        { level: 'DEBUG' },
        'test-token',
      )
    })
  })

  it('Apply button is disabled when selected level matches current', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ level: 'INFO' })
    renderSettings()
    await waitFor(() => expect(screen.getByRole('button', { name: /apply/i })).toBeDisabled())
  })
})
