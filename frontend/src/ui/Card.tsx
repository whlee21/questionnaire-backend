import React from 'react'
interface CardProps { children: React.ReactNode; title?: string; style?: React.CSSProperties }
export function Card({ children, title, style }: CardProps) {
  return (
    <div style={{ backgroundColor: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)', boxShadow: 'var(--shadow-sm)', ...style }}>
      {title && <h2 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-lg)', fontWeight: 600 }}>{title}</h2>}
      {children}
    </div>
  )
}
