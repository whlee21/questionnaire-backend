import React, { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Textarea } from '../ui/Textarea'
import { Table } from '../ui/Table'
import { Card } from '../ui/Card'

interface Topic { topic: string; subscriber_count: number }

export default function TopicsPage() {
  const { token } = useAuth()
  const { addToast } = useToast()
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(false)
  const [subTopic, setSubTopic] = useState('')
  const [subTokens, setSubTokens] = useState('')
  const [unsubTopic, setUnsubTopic] = useState('')
  const [unsubTokens, setUnsubTokens] = useState('')
  const [subLoading, setSubLoading] = useState(false)
  const [unsubLoading, setUnsubLoading] = useState(false)

  const fetchTopics = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiClient.get<Topic[]>('/api/v1/topics', token)
      setTopics(data)
    } catch { addToast('Failed to load topics', 'error') }
    finally { setLoading(false) }
  }, [token, addToast])

  useEffect(() => { fetchTopics() }, [fetchTopics])

  const parseTokens = (raw: string) => raw.split(',').map(t => t.trim()).filter(Boolean)

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    const tokens = parseTokens(subTokens)
    if (tokens.length > 1000) addToast('Warning: max 1000 tokens per request', 'warning')
    setSubLoading(true)
    try {
      const res = await apiClient.post<{ subscribed: number }>('/api/v1/topics/subscribe', { topic: subTopic, tokens: tokens.slice(0, 1000) }, token)
      addToast(`Subscribed ${res.subscribed} tokens to "${subTopic}"`, 'success')
      setSubTopic(''); setSubTokens(''); fetchTopics()
    } catch (err) { addToast(err instanceof Error ? err.message : 'Subscribe failed', 'error') }
    finally { setSubLoading(false) }
  }

  const handleUnsubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    const tokens = parseTokens(unsubTokens)
    setUnsubLoading(true)
    try {
      const res = await apiClient.post<{ unsubscribed: number }>('/api/v1/topics/unsubscribe', { topic: unsubTopic, tokens: tokens.slice(0, 1000) }, token)
      addToast(`Unsubscribed ${res.unsubscribed} tokens from "${unsubTopic}"`, 'success')
      setUnsubTopic(''); setUnsubTokens(''); fetchTopics()
    } catch (err) { addToast(err instanceof Error ? err.message : 'Unsubscribe failed', 'error') }
    finally { setUnsubLoading(false) }
  }

  const columns = [
    { key: 'topic', header: 'Topic' },
    { key: 'subscriber_count', header: 'Subscribers' },
  ]

  return (
    <div>
      <h1 style={{ margin: '0 0 24px', fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Topics</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <Card title="Subscribe">
          <form onSubmit={handleSubscribe} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="Topic" value={subTopic} onChange={e => setSubTopic(e.target.value)} placeholder="news" required />
            <Textarea label="Tokens (comma-separated)" value={subTokens} onChange={e => setSubTokens(e.target.value)} placeholder="tok-1, tok-2, ..." hint={parseTokens(subTokens).length > 1000 ? '⚠️ Max 1000 tokens' : undefined} />
            <Button type="submit" loading={subLoading} size="sm">Subscribe</Button>
          </form>
        </Card>
        <Card title="Unsubscribe">
          <form onSubmit={handleUnsubscribe} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Input label="Topic" value={unsubTopic} onChange={e => setUnsubTopic(e.target.value)} placeholder="news" required />
            <Textarea label="Tokens (comma-separated)" value={unsubTokens} onChange={e => setUnsubTokens(e.target.value)} placeholder="tok-1, tok-2, ..." />
            <Button type="submit" variant="secondary" loading={unsubLoading} size="sm">Unsubscribe</Button>
          </form>
        </Card>
      </div>
      <Card title="Active Topics">
        <Table columns={columns} data={topics as unknown as Record<string, unknown>[]} keyField="topic" loading={loading} emptyMessage="No topics yet. Subscribe devices to create topics." />
      </Card>
    </div>
  )
}
