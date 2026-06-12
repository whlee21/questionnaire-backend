interface SpinnerProps { size?: number; color?: string }
export function Spinner({ size = 20, color = 'var(--color-accent)' }: SpinnerProps) {
  return <div role="status" aria-label="Loading" style={{ width: size, height: size, border: `2px solid ${color}20`, borderTopColor: color, borderRadius: '50%', animation: 'spin 0.6s linear infinite', display: 'inline-block' }} />
}
