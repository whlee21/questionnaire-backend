import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import DevicesPage from '../pages/DevicesPage'

vi.mock('../api/client', () => ({
  apiClient: { post: vi.fn(), get: vi.fn(), delete: vi.fn(), put: vi.fn() },
}))

import { apiClient } from '../api/client'

function renderDevices() {
  localStorage.setItem('pushnotify_token', 'test-token')
  return render(
    <MemoryRouter initialEntries={['/devices']}>
      <AuthProvider>
        <ToastProvider>
          <Routes><Route path="/devices" element={<DevicesPage />} /></Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('DevicesPage', () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.setItem('pushnotify_token', 'test-token') })

  it('shows empty state when no devices', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ items: [], total: 0, page: 1, size: 20 })
    renderDevices()
    await waitFor(() => { expect(screen.getByText(/no devices/i)).toBeInTheDocument() })
  })

  it('renders device table with data', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      items: [{ id: 'dev-1', platform: 'android', app_version: '1.0', fcm_token_masked: 'tok-...XXXX', push_enabled: true, external_user_id: null, last_seen_at: new Date().toISOString(), created_at: new Date().toISOString() }],
      total: 1, page: 1, size: 20,
    })
    renderDevices()
    await waitFor(() => {
      expect(screen.getByText('android')).toBeInTheDocument()
      expect(screen.getByText('tok-...XXXX')).toBeInTheDocument()
    })
  })
})
