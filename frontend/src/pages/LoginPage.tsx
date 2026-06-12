import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { apiClient } from '../api/client'

interface TokenOut {
  access_token: string
  token_type: string
}

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const { addToast } = useToast()
  const navigate = useNavigate()

  const validate = (): boolean => {
    let valid = true
    if (!email.trim()) {
      setEmailError('Email is required')
      valid = false
    } else {
      setEmailError('')
    }
    if (!password) {
      setPasswordError('Password is required')
      valid = false
    } else {
      setPasswordError('')
    }
    return valid
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    setLoading(true)
    try {
      const data = await apiClient.post<TokenOut>('/api/v1/auth/login', { email, password })
      login(data.access_token)
      navigate('/compose', { replace: true })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      addToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--color-bg-subtle)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '40px',
          width: '100%',
          maxWidth: '400px',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <h1
          style={{
            margin: '0 0 8px',
            fontSize: 'var(--text-2xl)',
            fontWeight: 700,
            color: 'var(--color-text)',
          }}
        >
          PushNotify
        </h1>
        <p style={{ margin: '0 0 32px', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
          Sign in to your admin console
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              error={emailError}
              placeholder="admin@example.com"
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              error={passwordError}
              placeholder="Enter password"
              autoComplete="current-password"
            />
            <Button
              type="submit"
              loading={loading}
              style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
            >
              Sign in
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
