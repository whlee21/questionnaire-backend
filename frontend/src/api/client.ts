const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type RequestOptions = {
  method?: string
  body?: unknown
  token?: string | null
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (options.token) {
    headers['Authorization'] = `Bearer ${options.token}`
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail ?? 'Request failed')
  }

  if (response.status === 204) return undefined as T
  return response.json()
}

export const apiClient = {
  get: <T>(path: string, token?: string | null) =>
    request<T>(path, { token }),
  post: <T>(path: string, body: unknown, token?: string | null) =>
    request<T>(path, { method: 'POST', body, token }),
  put: <T>(path: string, body: unknown, token?: string | null) =>
    request<T>(path, { method: 'PUT', body, token }),
  delete: <T>(path: string, token?: string | null) =>
    request<T>(path, { method: 'DELETE', token }),
}
