import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { apiClient } from '../api/client'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Textarea } from '../ui/Textarea'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'

type TargetType = 'broadcast' | 'token' | 'tokens' | 'topic'

interface SendResult {
  success_count: number
  failure_count: number
  invalidated_tokens: string[]
  dry_run: boolean
}

export default function ComposePage() {
  const { token } = useAuth()
  const { addToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SendResult | null>(null)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [targetType, setTargetType] = useState<TargetType>('broadcast')
  const [singleToken, setSingleToken] = useState('')
  const [tokenList, setTokenList] = useState('')
  const [topic, setTopic] = useState('')
  const [dryRun, setDryRun] = useState(false)
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [titleError, setTitleError] = useState('')
  const [bodyError, setBodyError] = useState('')

  const validate = (): boolean => {
    let valid = true
    if (!title.trim()) { setTitleError('Title is required'); valid = false } else setTitleError('')
    if (!body.trim()) { setBodyError('Body is required'); valid = false } else setBodyError('')
    return valid
  }

  const buildTarget = () => {
    switch (targetType) {
      case 'token': return { type: 'token' as const, token: singleToken }
      case 'tokens': return { type: 'tokens' as const, tokens: tokenList.split(',').map(t => t.trim()).filter(Boolean) }
      case 'topic': return { type: 'topic' as const, topic }
      default: return { type: 'broadcast' as const }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const res = await apiClient.post<SendResult>('/api/v1/messages/send', {
        target: buildTarget(),
        notification: { title, body, ...(imageUrl ? { image_url: imageUrl } : {}) },
        data: {},
        dry_run: dryRun,
        ...(idempotencyKey ? { idempotency_key: idempotencyKey } : {}),
      }, token)
      setResult(res)
      addToast(`Sent: ${res.success_count} success, ${res.failure_count} failed`, res.failure_count > 0 ? 'warning' : 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Send failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '720px' }}>
      <h1 style={{ margin: '0 0 24px', fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Compose & Send</h1>
      <Card>
        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input label="Title *" value={title} onChange={e => setTitle(e.target.value)} error={titleError} placeholder="Notification title" />
            <Textarea label="Body *" value={body} onChange={e => setBody(e.target.value)} error={bodyError} placeholder="Notification body" />
            <Input label="Image URL" value={imageUrl} onChange={e => setImageUrl(e.target.value)} placeholder="https://..." />

            <div>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 500, display: 'block', marginBottom: '8px' }}>Target</label>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                {(['broadcast', 'token', 'tokens', 'topic'] as TargetType[]).map(t => (
                  <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: 'var(--text-sm)' }}>
                    <input type="radio" name="targetType" value={t} checked={targetType === t} onChange={() => setTargetType(t)} />
                    {t === 'broadcast' ? 'Broadcast' : t === 'token' ? 'Single Token' : t === 'tokens' ? 'Token List' : 'Topic'}
                  </label>
                ))}
              </div>
            </div>

            {targetType === 'token' && <Input label="FCM Token" value={singleToken} onChange={e => setSingleToken(e.target.value)} placeholder="FCM registration token" />}
            {targetType === 'tokens' && <Textarea label="Token List (comma-separated)" value={tokenList} onChange={e => setTokenList(e.target.value)} placeholder="tok-1, tok-2, tok-3" />}
            {targetType === 'topic' && <Input label="Topic Name" value={topic} onChange={e => setTopic(e.target.value)} placeholder="news" />}

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: 'var(--text-sm)' }}>
              <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} />
              Dry run (validate only, no delivery)
            </label>

            <Input label="Idempotency Key (optional)" value={idempotencyKey} onChange={e => setIdempotencyKey(e.target.value)} placeholder="unique-key-for-dedup" />

            <Button type="submit" loading={loading} style={{ alignSelf: 'flex-start' }}>
              {dryRun ? 'Validate (Dry Run)' : 'Send Notification'}
            </Button>
          </div>
        </form>
      </Card>

      {result && (
        <Card title="Send Result" style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <Badge variant="success">Success: {result.success_count}</Badge>
            <Badge variant={result.failure_count > 0 ? 'error' : 'default'}>Failed: {result.failure_count}</Badge>
            {result.dry_run && <Badge variant="info">Dry Run</Badge>}
          </div>
          {result.invalidated_tokens.length > 0 && (
            <div style={{ marginTop: '12px', fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
              Invalidated tokens: {result.invalidated_tokens.length}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
