import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'

type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

const LOG_LEVEL_OPTIONS: { value: string; label: string }[] = [
  { value: 'DEBUG', label: 'DEBUG' },
  { value: 'INFO', label: 'INFO' },
  { value: 'WARNING', label: 'WARNING' },
  { value: 'ERROR', label: 'ERROR' },
  { value: 'CRITICAL', label: 'CRITICAL' },
]

const LEVEL_VARIANT: Record<LogLevel, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  DEBUG: 'default',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'error',
}

export default function SettingsPage() {
  const { token } = useAuth()
  const { addToast } = useToast()
  const [currentLevel, setCurrentLevel] = useState<LogLevel | null>(null)
  const [selectedLevel, setSelectedLevel] = useState<LogLevel>('INFO')
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  useEffect(() => {
    setFetching(true)
    apiClient
      .get<{ level: LogLevel }>('/api/v1/admin/log-level', token)
      .then(data => {
        setCurrentLevel(data.level)
        setSelectedLevel(data.level)
      })
      .catch(err => addToast(err instanceof Error ? err.message : 'Failed to fetch log level', 'error'))
      .finally(() => setFetching(false))
  }, [token])

  const handleApply = async () => {
    setLoading(true)
    try {
      const data = await apiClient.put<{ level: LogLevel }>(
        '/api/v1/admin/log-level',
        { level: selectedLevel },
        token,
      )
      setCurrentLevel(data.level)
      addToast(`Log level set to ${data.level}`, 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to update log level', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '480px' }}>
      <h1 style={{ margin: '0 0 24px', fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Settings</h1>
      <Card title="Logging">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>Current level:</span>
            {fetching ? (
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>Loading…</span>
            ) : currentLevel ? (
              <Badge variant={LEVEL_VARIANT[currentLevel]}>{currentLevel}</Badge>
            ) : null}
          </div>
          <Select
            label="New level"
            value={selectedLevel}
            options={LOG_LEVEL_OPTIONS}
            onChange={e => setSelectedLevel(e.target.value as LogLevel)}
          />
          <Button
            onClick={handleApply}
            loading={loading}
            disabled={fetching || selectedLevel === currentLevel}
            style={{ alignSelf: 'flex-start' }}
          >
            Apply
          </Button>
        </div>
      </Card>
    </div>
  )
}
