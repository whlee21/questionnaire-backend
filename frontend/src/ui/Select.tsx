import React from 'react'
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string; error?: string; options: { value: string; label: string }[]
}
export function Select({ label, error, id, options, style, ...props }: SelectProps) {
  const sid = id ?? label?.toLowerCase().replace(/\s+/g, '-')
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && <label htmlFor={sid} style={{ fontSize: 'var(--text-sm)', fontWeight: 500 }}>{label}</label>}
      <select id={sid} style={{ padding: '8px 12px', border: `1px solid ${error ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-sans)', backgroundColor: 'var(--color-bg)', width: '100%', ...style }} {...props}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      {error && <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-error)' }}>{error}</span>}
    </div>
  )
}
