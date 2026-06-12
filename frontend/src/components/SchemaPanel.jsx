import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchSchema } from '../store/querySlice'

export default function SchemaPanel() {
  const dispatch = useDispatch()
  const { schema } = useSelector(s => s.query)
  const [open, setOpen] = useState({})

  useEffect(() => { dispatch(fetchSchema()) }, [])

  const toggle = (t) => setOpen(p => ({...p, [t]: !p[t]}))

  if (!schema) return <div className="schema-loading">Loading schema...</div>

  return (
    <div className="schema-panel">
      <div className="schema-header">
        <span className="schema-title">Database Schema</span>
        <span className="schema-count">{Object.keys(schema).length} tables</span>
      </div>
      {Object.entries(schema).map(([table, cols]) => (
        <div key={table} className="schema-table">
          <div className="schema-table-header" onClick={() => toggle(table)}>
            <span className="table-icon">⊞</span>
            <span className="table-name">{table}</span>
            <span className="col-count">{cols.length} cols</span>
            <span className="chevron">{open[table] ? '▲' : '▼'}</span>
          </div>
          {open[table] && (
            <div className="schema-cols">
              {cols.map(c => (
                <div key={c.name} className="schema-col">
                  <span className="col-name">{c.name}</span>
                  <span className="col-type">{c.type.toLowerCase()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
