import React from 'react'
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string; error?: string
}
export function Textarea({ label, error, id, style, ...props }: TextareaProps) {
  const tid = id ?? label?.toLowerCase().replace(/\s+/g, '-')
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && <label htmlFor={tid} style={{ fontSize: 'var(--text-sm)', fontWeight: 500 }}>{label}</label>}
      <textarea id={tid} style={{ padding: '8px 12px', border: `1px solid ${error ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-sans)', resize: 'vertical', minHeight: '80px', width: '100%', boxSizing: 'border-box' as const, ...style }} {...props} />
      {error && <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-error)' }}>{error}</span>}
    </div>
  )
}
