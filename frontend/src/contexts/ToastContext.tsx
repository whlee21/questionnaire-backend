import React, { createContext, useContext, useState, useCallback } from 'react'
type ToastType = 'success' | 'error' | 'info' | 'warning'
interface Toast { id: string; message: string; type: ToastType }
interface ToastContextType { addToast: (message: string, type?: ToastType) => void }
const ToastContext = createContext<ToastContextType | null>(null)
const toastColors: Record<ToastType, string> = { success: '#10b981', error: '#ef4444', info: '#6366f1', warning: '#f59e0b' }

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])
  const remove = (id: string) => setToasts(prev => prev.filter(t => t.id !== id))
  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {toasts.map(t => (
          <div key={t.id} onClick={() => remove(t.id)} style={{ backgroundColor: toastColors[t.type], color: '#fff', padding: '12px 16px', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)', display: 'flex', alignItems: 'center', gap: '8px', minWidth: '280px', maxWidth: '400px', cursor: 'pointer' }}>
            <span style={{ flex: 1, fontSize: 'var(--text-sm)' }}>{t.message}</span>
            <span style={{ opacity: 0.7 }}>x</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
