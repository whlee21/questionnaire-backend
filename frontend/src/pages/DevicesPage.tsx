import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { Table } from '../ui/Table'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'

interface Device {
  id: string
  platform: 'ios' | 'android' | 'web'
  app_version: string
  fcm_token_masked: string
  push_enabled: boolean
  external_user_id: string | null
  last_seen_at: string
  created_at: string
}

interface DevicesResponse {
  items: Device[]
  total: number
  page: number
  size: number
}

export default function DevicesPage() {
  const { token } = useAuth()
  const { addToast } = useToast()
  const [devices, setDevices] = useState<Device[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [platform, setPlatform] = useState('')
  const [loading, setLoading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchDevices = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), size: '20' })
      if (platform) params.set('platform', platform)
      const data = await apiClient.get<DevicesResponse>(`/api/v1/devices?${params}`, token)
      setDevices(data.items)
      setTotal(data.total)
    } catch {
      addToast('Failed to load devices', 'error')
    } finally {
      setLoading(false)
    }
  }, [token, page, platform, addToast])

  useEffect(() => { fetchDevices() }, [fetchDevices])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this device?')) return
    setDeletingId(id)
    try {
      await apiClient.delete(`/api/v1/devices/${id}`, token)
      addToast('Device deleted', 'success')
      fetchDevices()
    } catch {
      addToast('Failed to delete device', 'error')
    } finally {
      setDeletingId(null)
    }
  }

  const columns = [
    { key: 'platform', header: 'Platform', render: (d: Device) => <Badge variant="info">{d.platform}</Badge> },
    { key: 'fcm_token_masked', header: 'Token' },
    { key: 'app_version', header: 'Version' },
    { key: 'push_enabled', header: 'Status', render: (d: Device) => <Badge variant={d.push_enabled ? 'success' : 'error'}>{d.push_enabled ? 'Active' : 'Disabled'}</Badge> },
    { key: 'last_seen_at', header: 'Last Seen', render: (d: Device) => new Date(d.last_seen_at).toLocaleDateString() },
    { key: 'actions', header: '', render: (d: Device) => (
      <Button variant="danger" size="sm" loading={deletingId === d.id} onClick={() => handleDelete(d.id)}>Delete</Button>
    )},
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Devices</h1>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Select
            options={[
              { value: '', label: 'All platforms' },
              { value: 'ios', label: 'iOS' },
              { value: 'android', label: 'Android' },
              { value: 'web', label: 'Web' },
            ]}
            value={platform}
            onChange={e => { setPlatform(e.target.value); setPage(1) }}
            style={{ width: '160px' }}
          />
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>{total} total</span>
        </div>
      </div>
      <Card>
        <Table<Device>
          columns={columns}
          data={devices}
          keyField="id"
          loading={loading}
          emptyMessage="No devices registered yet"
        />
      </Card>
      {total > 20 && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'center' }}>
          <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span style={{ fontSize: 'var(--text-sm)', padding: '8px' }}>Page {page}</span>
          <Button variant="ghost" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}
    </div>
  )
}
