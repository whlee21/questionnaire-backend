import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import TopicsPage from '../pages/TopicsPage'

vi.mock('../api/client', () => ({
  apiClient: { post: vi.fn(), get: vi.fn(), delete: vi.fn(), put: vi.fn() },
}))

import { apiClient } from '../api/client'

function renderTopics() {
  localStorage.setItem('pushnotify_token', 'test-token')
  return render(
    <MemoryRouter initialEntries={['/topics']}>
      <AuthProvider>
        <ToastProvider>
          <Routes><Route path="/topics" element={<TopicsPage />} /></Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('TopicsPage', () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.setItem('pushnotify_token', 'test-token') })

  it('renders topics page with subscribe/unsubscribe forms', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce([])
    renderTopics()
    await waitFor(() => { expect(screen.getByRole('heading', { name: /^topics$/i, level: 1 })).toBeInTheDocument() })
    expect(screen.getByRole('button', { name: /^subscribe$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^unsubscribe$/i })).toBeInTheDocument()
  })

  it('shows empty state when no topics', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce([])
    renderTopics()
    await waitFor(() => { expect(screen.getByText(/no topics yet/i)).toBeInTheDocument() })
  })
})
