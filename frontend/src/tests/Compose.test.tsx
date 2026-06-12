import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ToastProvider } from '../contexts/ToastContext'
import ComposePage from '../pages/ComposePage'

vi.mock('../api/client', () => ({
  apiClient: { post: vi.fn(), get: vi.fn(), delete: vi.fn(), put: vi.fn() },
}))

import { apiClient } from '../api/client'

function renderCompose() {
  localStorage.setItem('pushnotify_token', 'test-token')
  return render(
    <MemoryRouter initialEntries={['/compose']}>
      <AuthProvider>
        <ToastProvider>
          <Routes><Route path="/compose" element={<ComposePage />} /></Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('ComposePage', () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.setItem('pushnotify_token', 'test-token') })

  it('renders compose form with heading', () => {
    renderCompose()
    expect(screen.getByRole('heading', { name: /compose/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
  })

  it('shows validation errors when title and body are empty', async () => {
    renderCompose()
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument()
      expect(screen.getByText('Body is required')).toBeInTheDocument()
    })
  })

  it('submits with broadcast target by default', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ success_count: 1, failure_count: 0, invalidated_tokens: [], dry_run: false })
    renderCompose()
    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: 'Hello' } })
    fireEvent.change(screen.getByLabelText(/body/i), { target: { value: 'World' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/messages/send',
        expect.objectContaining({ target: { type: 'broadcast' } }),
        'test-token',
      )
    })
  })

  it('shows result panel after successful send', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ success_count: 5, failure_count: 1, invalidated_tokens: ['tok-dead'], dry_run: false })
    renderCompose()
    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: 'T' } })
    fireEvent.change(screen.getByLabelText(/body/i), { target: { value: 'B' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() => {
      expect(screen.getByText(/success: 5/i)).toBeInTheDocument()
    })
  })
})
