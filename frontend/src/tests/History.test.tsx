import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import HistoryPage from '../pages/HistoryPage'

vi.mock('../api/client', () => ({
  apiClient: { post: vi.fn(), get: vi.fn(), delete: vi.fn(), put: vi.fn() },
}))

import { apiClient } from '../api/client'

function renderHistory() {
  localStorage.setItem('pushnotify_token', 'test-token')
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <AuthProvider>
        <ToastProvider>
          <Routes><Route path="/history" element={<HistoryPage />} /></Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('HistoryPage', () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.setItem('pushnotify_token', 'test-token') })

  it('shows empty state when no history', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ items: [], total: 0, page: 1, size: 20 })
    renderHistory()
    await waitFor(() => { expect(screen.getByText(/no send history/i)).toBeInTheDocument() })
  })

  it('renders history table with data', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      items: [{ id: 'evt-1', actor: 'admin@example.com', target_type: 'broadcast', target_summary: 'all', payload_summary: { title: 'Hello', body: 'World' }, dry_run: false, success_count: 10, failure_count: 0, created_at: new Date().toISOString() }],
      total: 1, page: 1, size: 20,
    })
    renderHistory()
    await waitFor(() => {
      expect(screen.getByText('broadcast')).toBeInTheDocument()
      expect(screen.getByText('all')).toBeInTheDocument()
    })
  })
})
