import React from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: { backgroundColor: 'var(--color-accent)', color: '#fff', border: 'none' },
  secondary: { backgroundColor: 'transparent', color: 'var(--color-accent)', border: '1px solid var(--color-accent)' },
  danger: { backgroundColor: 'var(--color-error)', color: '#fff', border: 'none' },
  ghost: { backgroundColor: 'transparent', color: 'var(--color-text)', border: '1px solid var(--color-border)' },
}

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: { padding: '4px 12px', fontSize: 'var(--text-sm)' },
  md: { padding: '8px 16px', fontSize: 'var(--text-sm)' },
  lg: { padding: '10px 20px', fontSize: 'var(--text-base)' },
}

export function Button({ variant = 'primary', size = 'md', loading = false, disabled, children, style, ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      style={{
        ...variantStyles[variant],
        ...sizeStyles[size],
        borderRadius: 'var(--radius-md)',
        fontFamily: 'var(--font-sans)',
        fontWeight: 500,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.6 : 1,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        transition: 'opacity 0.15s',
        ...style,
      }}
      {...props}
    >
      {loading ? '...' : children}
    </button>
  )
}
