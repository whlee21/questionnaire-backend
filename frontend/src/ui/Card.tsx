import React from 'react'
interface CardProps extends React.HTMLAttributes<HTMLDivElement> { children: React.ReactNode; title?: string; style?: React.CSSProperties }
export function Card({ children, title, style, ...rest }: CardProps) {
  return (
    <div style={{ backgroundColor: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)', boxShadow: 'var(--shadow-sm)', ...style }} {...rest}>
      {title && <h2 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-lg)', fontWeight: 600 }}>{title}</h2>}
      {children}
    </div>
  )
}
