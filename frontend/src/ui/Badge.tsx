import React from 'react'
type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info'
interface BadgeProps { children: React.ReactNode; variant?: BadgeVariant }
const colors: Record<BadgeVariant, { bg: string; color: string }> = {
  default: { bg: 'var(--color-bg-subtle)', color: 'var(--color-text-muted)' },
  success: { bg: '#d1fae5', color: '#065f46' },
  warning: { bg: '#fef3c7', color: '#92400e' },
  error: { bg: 'var(--color-error-light)', color: 'var(--color-error)' },
  info: { bg: 'var(--color-accent-light)', color: 'var(--color-accent)' },
}
export function Badge({ children, variant = 'default' }: BadgeProps) {
  const { bg, color } = colors[variant]
  return <span style={{ display: 'inline-flex', alignItems: 'center', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontSize: 'var(--text-xs)', fontWeight: 500, backgroundColor: bg, color }}>{children}</span>
}
