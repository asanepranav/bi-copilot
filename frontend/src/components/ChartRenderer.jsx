import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#6366f1','#06b6d4','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6']

const fmt = (v) => {
  if (typeof v === 'number') {
    if (v >= 1_000_000) return `${(v/1_000_000).toFixed(1)}M`
    if (v >= 1_000)     return `${(v/1_000).toFixed(1)}K`
    if (v % 1 !== 0)    return v.toFixed(2)
    return v.toString()
  }
  return v
}

function DataTable({ columns, rows }) {
  if (!rows?.length) return <div className="no-data">No data returned</div>
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map(c => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map(c => <td key={c}>{row[c] ?? '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function NumberCard({ rows, columns }) {
  const val = rows?.[0]?.[columns?.[0]]
  return (
    <div className="number-card">
      <div className="number-value">{fmt(val)}</div>
      <div className="number-label">{columns?.[0]?.replace(/_/g,' ')}</div>
    </div>
  )
}

export default function ChartRenderer({ data, chartType }) {
  if (!data?.rows?.length) return <div className="no-data">No results</div>

  const { columns, rows } = data
  const numCols  = columns.filter(c => rows.some(r => typeof r[c] === 'number'))
  const strCols  = columns.filter(c => rows.some(r => typeof r[c] === 'string'))
  const xKey     = strCols[0] || columns[0]
  const yKey     = numCols[0] || columns[1] || columns[0]

  if (chartType === 'number' || (rows.length === 1 && columns.length === 1)) {
    return <NumberCard rows={rows} columns={columns} />
  }

  if (chartType === 'table' || rows.length > 50) {
    return <DataTable columns={columns} rows={rows} />
  }

  if (chartType === 'pie' && rows.length <= 10) {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie data={rows} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={110} label={({name, percent}) => `${name} ${(percent*100).toFixed(0)}%`}>
            {rows.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={(v) => fmt(v)} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{top:8,right:24,left:0,bottom:8}}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey={xKey} tick={{fontSize:12,fill:'var(--muted)'}} />
          <YAxis tickFormatter={fmt} tick={{fontSize:12,fill:'var(--muted)'}} />
          <Tooltip formatter={(v) => fmt(v)} contentStyle={{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:8,fontSize:13}} />
          <Legend />
          {numCols.map((col, i) => (
            <Line key={col} type="monotone" dataKey={col} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{r:3}} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  // default: bar
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={rows} margin={{top:8,right:24,left:0,bottom:8}}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey={xKey} tick={{fontSize:11,fill:'var(--muted)'}} />
        <YAxis tickFormatter={fmt} tick={{fontSize:12,fill:'var(--muted)'}} />
        <Tooltip formatter={(v) => fmt(v)} contentStyle={{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:8,fontSize:13}} />
        <Legend />
        {numCols.map((col, i) => (
          <Bar key={col} dataKey={col} fill={COLORS[i % COLORS.length]} radius={[4,4,0,0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
