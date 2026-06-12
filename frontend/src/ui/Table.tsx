import React from 'react'
interface Column<T> { key: string; header: string; render?: (row: T) => React.ReactNode; width?: string }
interface TableProps<T> { columns: Column<T>[]; data: T[]; keyField: keyof T; emptyMessage?: string; loading?: boolean }
export function Table<T extends Record<string, unknown>>({ columns, data, keyField, emptyMessage = 'No data', loading = false }: TableProps<T>) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-sm)' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
            {columns.map(col => <th key={col.key} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--color-text-muted)', width: col.width }}>{col.header}</th>)}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td colSpan={columns.length} style={{ padding: '24px', textAlign: 'center' }}>Loading...</td></tr>
          ) : data.length === 0 ? (
            <tr><td colSpan={columns.length} style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>{emptyMessage}</td></tr>
          ) : data.map(row => (
            <tr key={String(row[keyField])} style={{ borderBottom: '1px solid var(--color-border)' }}>
              {columns.map(col => <td key={col.key} style={{ padding: '10px 12px' }}>{col.render ? col.render(row) : String(row[col.key] ?? '')}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
