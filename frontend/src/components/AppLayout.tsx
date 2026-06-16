import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { to: '/compose', label: 'Compose & Send', icon: 'envelope' },
  { to: '/devices', label: 'Devices', icon: 'phone' },
  { to: '/topics', label: 'Topics', icon: 'broadcast' },
  { to: '/history', label: 'Send History', icon: 'list' },
  { to: '/settings', label: 'Settings', icon: 'gear' },
]

export function AppLayout() {
  const { logout } = useAuth()
  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'var(--font-sans)' }}>
      <aside style={{ width: 'var(--sidebar-width)', backgroundColor: 'var(--color-sidebar)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: 'var(--text-lg)' }}>PushNotify</span>
        </div>
        <nav style={{ flex: 1, padding: '12px 8px' }}>
          {navItems.map(item => (
            <NavLink key={item.to} to={item.to} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px',
              borderRadius: 'var(--radius-md)', textDecoration: 'none', fontSize: 'var(--text-sm)',
              fontWeight: 500, marginBottom: '2px', transition: 'background-color 0.15s',
              color: isActive ? 'var(--color-text-sidebar-active)' : 'var(--color-text-sidebar)',
              backgroundColor: isActive ? 'var(--color-sidebar-active)' : 'transparent',
            })}>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: '12px 8px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <button onClick={logout} style={{ width: '100%', padding: '8px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-sidebar)', fontSize: 'var(--text-sm)', cursor: 'pointer', textAlign: 'left' }}>
            Sign out
          </button>
        </div>
      </aside>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{ height: 'var(--topbar-height)', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', padding: '0 24px', backgroundColor: 'var(--color-bg)', flexShrink: 0 }}>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>Admin Console</span>
        </header>
        <main style={{ flex: 1, overflow: 'auto', padding: '24px', backgroundColor: 'var(--color-bg-subtle)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
