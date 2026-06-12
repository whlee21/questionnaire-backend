import React, { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import { Select } from '../ui/Select'
import { Table } from '../ui/Table'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'

interface SendEvent {
  id: string
  actor: string
  target_type: string
  target_summary: string
  payload_summary: { title: string; body: string }
  dry_run: boolean
  success_count: number
  failure_count: number
  created_at: string
}

interface HistoryResponse {
  items: SendEvent[]
  total: number
  page: number
  size: number
}

export default function HistoryPage() {
  const { token } = useAuth()
  const { addToast } = useToast()
  const [events, setEvents] = useState<SendEvent[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [targetType, setTargetType] = useState('')
  const [dryRunFilter, setDryRunFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<SendEvent | null>(null)

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), size: '20' })
      if (targetType) params.set('target_type', targetType)
      if (dryRunFilter !== '') params.set('dry_run', dryRunFilter)
      const data = await apiClient.get<HistoryResponse>(`/api/v1/messages/history?${params}`, token)
      setEvents(data.items)
      setTotal(data.total)
    } catch { addToast('Failed to load history', 'error') }
    finally { setLoading(false) }
  }, [token, page, targetType, dryRunFilter, addToast])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  const columns = [
    { key: 'created_at', header: 'Time', render: (e: SendEvent) => new Date(e.created_at).toLocaleString() },
    { key: 'target_type', header: 'Target', render: (e: SendEvent) => <Badge variant="info">{e.target_type}</Badge> },
    { key: 'target_summary', header: 'Summary' },
    { key: 'dry_run', header: 'Mode', render: (e: SendEvent) => e.dry_run ? <Badge variant="warning">Dry Run</Badge> : <Badge variant="success">Live</Badge> },
    { key: 'counts', header: 'Results', render: (e: SendEvent) => <span style={{ fontSize: 'var(--text-xs)' }}>✓{e.success_count} ✗{e.failure_count}</span> },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Send History</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Select
            options={[{ value: '', label: 'All types' }, { value: 'token', label: 'Single Token' }, { value: 'tokens', label: 'Token List' }, { value: 'topic', label: 'Topic' }, { value: 'broadcast', label: 'Broadcast' }]}
            value={targetType}
            onChange={e => { setTargetType(e.target.value); setPage(1) }}
            style={{ width: '140px' }}
          />
          <Select
            options={[{ value: '', label: 'All modes' }, { value: 'false', label: 'Live only' }, { value: 'true', label: 'Dry run only' }]}
            value={dryRunFilter}
            onChange={e => { setDryRunFilter(e.target.value); setPage(1) }}
            style={{ width: '140px' }}
          />
        </div>
      </div>
      <Card>
        <Table
          columns={columns}
          data={events as unknown as Record<string, unknown>[]}
          keyField="id"
          loading={loading}
          emptyMessage="No send history yet"
        />
      </Card>
      {total > 20 && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'center' }}>
          <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span style={{ fontSize: 'var(--text-sm)', padding: '8px' }}>Page {page} of {Math.ceil(total / 20)}</span>
          <Button variant="ghost" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}
      {selected && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setSelected(null)}>
          <Card style={{ maxWidth: '480px', width: '100%', margin: '24px' }} onClick={(e: React.MouseEvent) => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 16px' }}>Send Event Detail</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: 'var(--text-sm)' }}>
              <div><strong>Target:</strong> {selected.target_type} — {selected.target_summary}</div>
              <div><strong>Title:</strong> {selected.payload_summary.title}</div>
              <div><strong>Body:</strong> {selected.payload_summary.body}</div>
              <div><strong>Results:</strong> {selected.success_count} success, {selected.failure_count} failed</div>
              <div><strong>Mode:</strong> {selected.dry_run ? 'Dry Run' : 'Live'}</div>
              <div><strong>Actor:</strong> {selected.actor}</div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSelected(null)} style={{ marginTop: '16px' }}>Close</Button>
          </Card>
        </div>
      )}
    </div>
  )
}
