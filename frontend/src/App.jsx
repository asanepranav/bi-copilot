import { useState, useRef, useEffect } from 'react'
import { Provider, useDispatch, useSelector } from 'react-redux'
import { store } from './store/index'
import { runQuery, fetchSuggestions, executeRawSQL, setActiveTab, clearError } from './store/querySlice'
import ChartRenderer from './components/ChartRenderer'
import SchemaPanel from './components/SchemaPanel'

const css = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #0a0b0f;
  --surface:  #111318;
  --surface2: #181c24;
  --surface3: #1e2330;
  --border:   #252b3b;
  --border2:  #2e3650;
  --text:     #e8eaf0;
  --muted:    #5a6480;
  --muted2:   #7b88a8;
  --accent:   #6366f1;
  --accent2:  #818cf8;
  --cyan:     #06b6d4;
  --green:    #10b981;
  --amber:    #f59e0b;
  --red:      #ef4444;
  --radius:   10px;
  --font:     'DM Sans', sans-serif;
  --mono:     'JetBrains Mono', monospace;
}

body { background: var(--bg); color: var(--text); font-family: var(--font); height: 100vh; overflow: hidden; }

/* ── SHELL ── */
.app { display: grid; grid-template-columns: 260px 1fr; grid-template-rows: 52px 1fr; height: 100vh; }

/* ── TOPBAR ── */
.topbar {
  grid-column: 1 / -1;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 20px; gap: 16px;
}
.logo { display: flex; align-items: center; gap: 10px; margin-right: 16px; }
.logo-mark {
  width: 28px; height: 28px; background: var(--accent); border-radius: 7px;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.logo-text { font-size: 15px; font-weight: 700; letter-spacing: -.3px; }
.logo-text span { color: var(--muted2); font-weight: 400; }

.top-tabs { display: flex; gap: 2px; }
.top-tab {
  padding: 6px 14px; border-radius: 7px; font-size: 13px; font-weight: 500;
  cursor: pointer; border: none; background: none; color: var(--muted2);
  font-family: var(--font); transition: all .15s;
}
.top-tab:hover { background: var(--surface2); color: var(--text); }
.top-tab.active { background: var(--accent)22; color: var(--accent2); }

.top-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.status-pill { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--green); background: var(--green)11; border: 1px solid var(--green)33; padding: 4px 10px; border-radius: 20px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── SIDEBAR ── */
.sidebar {
  background: var(--surface); border-right: 1px solid var(--border);
  overflow-y: auto; display: flex; flex-direction: column;
}

/* ── SCHEMA ── */
.schema-panel { padding: 12px; flex: 1; }
.schema-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 6px 12px; }
.schema-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--muted2); }
.schema-count { font-size: 11px; background: var(--surface2); border: 1px solid var(--border); padding: 2px 8px; border-radius: 20px; color: var(--muted2); }
.schema-loading { padding: 20px; font-size: 13px; color: var(--muted); }
.schema-table { margin-bottom: 4px; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }
.schema-table-header { display: flex; align-items: center; gap: 8px; padding: 9px 12px; cursor: pointer; background: var(--surface2); transition: background .15s; }
.schema-table-header:hover { background: var(--surface3); }
.table-icon { font-size: 13px; color: var(--accent2); }
.table-name { font-size: 13px; font-weight: 500; font-family: var(--mono); flex: 1; }
.col-count { font-size: 11px; color: var(--muted); }
.chevron { font-size: 10px; color: var(--muted); }
.schema-cols { background: var(--surface); padding: 6px 0; }
.schema-col { display: flex; justify-content: space-between; padding: 5px 14px; font-size: 12px; }
.col-name { color: var(--text); font-family: var(--mono); }
.col-type { color: var(--cyan); font-family: var(--mono); font-size: 11px; }

/* ── HISTORY PANEL ── */
.history-panel { padding: 12px; }
.history-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--muted2); padding: 8px 6px 12px; }
.history-empty { font-size: 13px; color: var(--muted); padding: 8px 6px; }
.history-item { padding: 10px 12px; border-radius: var(--radius); cursor: pointer; border: 1px solid var(--border); margin-bottom: 6px; transition: all .15s; }
.history-item:hover { border-color: var(--accent); background: var(--accent)08; }
.history-q { font-size: 13px; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-meta { font-size: 11px; color: var(--muted); display: flex; gap: 8px; }
.chart-badge { background: var(--surface3); border: 1px solid var(--border); padding: 1px 7px; border-radius: 20px; }

/* ── MAIN ── */
.main { display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }

/* ── CHAT INPUT AREA ── */
.input-area { padding: 20px 24px; border-bottom: 1px solid var(--border); flex-shrink: 0; }

.input-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px;
  transition: border .15s;
}
.input-wrap:focus-within { border-color: var(--accent); }

.question-input {
  background: none; border: none; outline: none; width: 100%;
  font-size: 15px; color: var(--text); font-family: var(--font); resize: none;
  line-height: 1.5; min-height: 24px; max-height: 120px;
}
.question-input::placeholder { color: var(--muted); }

.input-actions { display: flex; align-items: center; justify-content: space-between; }
.input-left { display: flex; gap: 8px; }

.btn-run {
  background: var(--accent); color: white; border: none; border-radius: var(--radius);
  padding: 9px 20px; font-size: 13px; font-weight: 600; cursor: pointer;
  font-family: var(--font); display: flex; align-items: center; gap: 7px; transition: all .15s;
}
.btn-run:hover:not(:disabled) { background: #4f46e5; transform: translateY(-1px); }
.btn-run:disabled { opacity: .4; cursor: not-allowed; transform: none; }

.btn-ghost {
  background: none; border: 1px solid var(--border); color: var(--muted2);
  padding: 7px 14px; border-radius: var(--radius); font-size: 12px; font-weight: 500;
  cursor: pointer; font-family: var(--font); transition: all .15s;
}
.btn-ghost:hover { border-color: var(--border2); color: var(--text); }
.btn-ghost.active { border-color: var(--accent); color: var(--accent2); background: var(--accent)11; }

/* ── SUGGESTIONS ── */
.suggestions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.suggestion-chip {
  background: var(--surface); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 20px; font-size: 12px; color: var(--muted2);
  cursor: pointer; transition: all .15s; white-space: nowrap;
}
.suggestion-chip:hover { border-color: var(--accent); color: var(--accent2); background: var(--accent)08; }

/* ── SQL EDITOR ── */
.sql-editor-wrap { padding: 0 24px 16px; }
.sql-editor {
  width: 100%; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 14px; font-size: 13px;
  color: var(--cyan); font-family: var(--mono); outline: none; resize: vertical;
  min-height: 80px; transition: border .15s;
}
.sql-editor:focus { border-color: var(--accent); }
.sql-run-row { display: flex; justify-content: flex-end; margin-top: 8px; }

/* ── RESULTS AREA ── */
.results-area { flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }

.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: var(--muted); }
.empty-icon { font-size: 40px; opacity: .4; }
.empty-text { font-size: 14px; }

.result-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden; animation: fadeUp .25s ease;
}
@keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }

.result-header { padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 12px; }
.result-q { font-size: 14px; font-weight: 600; flex: 1; }
.result-time { font-size: 11px; color: var(--muted); }
.chart-type-tag { font-size: 11px; background: var(--surface3); border: 1px solid var(--border); padding: 2px 9px; border-radius: 20px; color: var(--accent2); font-family: var(--mono); }

.result-body { padding: 18px; }

/* ── SQL PREVIEW ── */
.sql-preview {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 14px; margin-bottom: 16px;
  display: flex; align-items: flex-start; gap: 12px;
}
.sql-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--muted2); white-space: nowrap; padding-top: 2px; }
.sql-code { font-family: var(--mono); font-size: 12px; color: var(--cyan); flex: 1; white-space: pre-wrap; line-height: 1.6; }

/* ── INSIGHT ── */
.insight-box {
  background: var(--accent)08; border: 1px solid var(--accent)22;
  border-radius: var(--radius); padding: 12px 14px; margin-top: 14px;
  display: flex; gap: 10px; align-items: flex-start;
}
.insight-icon { font-size: 16px; flex-shrink: 0; }
.insight-text { font-size: 13px; line-height: 1.6; color: var(--text); }

/* ── ERROR ── */
.error-bar { background: var(--red)11; border: 1px solid var(--red)33; color: var(--red); padding: 10px 16px; border-radius: var(--radius); font-size: 13px; display: flex; align-items: center; gap: 8px; margin: 0 24px 12px; }

/* ── LOADING ── */
.loading-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 24px 18px; display: flex; flex-direction: column; gap: 12px; }
.loading-bar { height: 4px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
.loading-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--cyan)); border-radius: 4px; animation: loading 1.5s ease-in-out infinite; }
@keyframes loading { 0%{width:0%;margin-left:0} 50%{width:70%;margin-left:15%} 100%{width:0%;margin-left:100%} }
.loading-steps { display: flex; gap: 20px; }
.loading-step { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--muted); }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--border2); }
.step-dot.active { background: var(--accent); animation: pulse 1s infinite; }

/* ── TABLE ── */
.table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: var(--surface2); padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--muted2); border-bottom: 1px solid var(--border); white-space: nowrap; }
.data-table td { padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--text); font-family: var(--mono); font-size: 12px; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface2); }

/* ── NUMBER CARD ── */
.number-card { display: flex; flex-direction: column; align-items: center; padding: 32px; gap: 8px; }
.number-value { font-size: 52px; font-weight: 700; color: var(--accent2); letter-spacing: -2px; font-family: var(--mono); }
.number-label { font-size: 14px; color: var(--muted2); text-transform: uppercase; letter-spacing: .5px; }

.no-data { font-size: 13px; color: var(--muted); padding: 20px; text-align: center; }

/* ── ROW COUNT ── */
.row-count { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
`

// ── Loading steps UI ──────────────────────────────────────────
function LoadingCard() {
  const [step, setStep] = useState(0)
  const steps = ['Writing SQL...', 'Validating query...', 'Executing on DB...', 'Generating insight...']
  useEffect(() => {
    const t = setInterval(() => setStep(p => (p + 1) % steps.length), 900)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="loading-card">
      <div className="loading-bar"><div className="loading-fill"/></div>
      <div className="loading-steps">
        {steps.map((s, i) => (
          <div key={i} className="loading-step">
            <div className={`step-dot ${i === step ? 'active' : ''}`}/>
            <span style={{color: i === step ? 'var(--text)' : 'var(--muted)'}}>{s}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Result card ───────────────────────────────────────────────
function ResultCard({ result }) {
  const [showSQL, setShowSQL] = useState(true)
  return (
    <div className="result-card">
      <div className="result-header">
        <span className="result-q">{result.question || 'Raw SQL'}</span>
        <span className="chart-type-tag">{result.chart_type}</span>
        <span className="result-time">{result.timestamp}</span>
      </div>
      <div className="result-body">
        {result.sql && result.sql !== 'raw' && (
          <div className="sql-preview">
            <span className="sql-label">SQL</span>
            <code className="sql-code">{result.sql}</code>
          </div>
        )}
        {result.data?.count !== undefined && (
          <div className="row-count">{result.data.count} rows returned</div>
        )}
        <ChartRenderer data={result.data} chartType={result.chart_type} />
        {result.insight && (
          <div className="insight-box">
            <span className="insight-icon">✦</span>
            <span className="insight-text">{result.insight}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main app ──────────────────────────────────────────────────
function BIApp() {
  const dispatch  = useDispatch()
  const { current, history, suggestions, loading, error, activeTab, sqlMode } = useSelector(s => s.query)

  const [question, setQuestion] = useState('')
  const [rawSQL,   setRawSQL]   = useState('')
  const inputRef = useRef(null)

  useEffect(() => { dispatch(fetchSuggestions()) }, [])

  const handleAsk = () => {
    if (!question.trim() || loading) return
    dispatch(runQuery(question.trim()))
    setQuestion('')
  }

  const handleRawSQL = () => {
    if (!rawSQL.trim() || loading) return
    dispatch(executeRawSQL(rawSQL.trim()))
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk() }
  }

  const useSuggestion = (s) => { setQuestion(s); inputRef.current?.focus() }

  return (
    <div className="app">
      <style>{css}</style>

      {/* ── TOPBAR ── */}
      <header className="topbar">
        <div className="logo">
          <div className="logo-mark">◈</div>
          <div className="logo-text">BI <span>Copilot</span></div>
        </div>
        <div className="top-tabs">
          {['chat','schema','history'].map(t => (
            <button key={t} className={`top-tab ${activeTab===t?'active':''}`} onClick={() => dispatch(setActiveTab(t))}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
        <div className="top-right">
          <div className="status-pill"><span className="status-dot"/>Connected</div>
        </div>
      </header>

      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        {activeTab === 'schema'  && <SchemaPanel />}
        {activeTab === 'history' && (
          <div className="history-panel">
            <div className="history-title">Query History</div>
            {!history.length && <div className="history-empty">No queries yet</div>}
            {history.map((h, i) => (
              <div key={i} className="history-item" onClick={() => dispatch(runQuery(h.question))}>
                <div className="history-q">{h.question}</div>
                <div className="history-meta">
                  <span className="chart-badge">{h.chart_type}</span>
                  <span>{h.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        )}
        {activeTab === 'chat' && <SchemaPanel />}
      </aside>

      {/* ── MAIN ── */}
      <main className="main">
        {/* Input */}
        <div className="input-area">
          <div className="input-wrap">
            <textarea
              ref={inputRef}
              className="question-input"
              rows={2}
              placeholder="Ask anything about your data... e.g. 'Show me total revenue by region this month'"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={handleKey}
            />
            <div className="input-actions">
              <div className="input-left">
                <button className={`btn-ghost ${sqlMode ? 'active' : ''}`} onClick={() => dispatch({type:'query/toggleSQLMode'})}>
                  ⌨ SQL Editor
                </button>
              </div>
              <button className="btn-run" onClick={handleAsk} disabled={loading || !question.trim()}>
                {loading ? <span style={{display:'inline-block',width:14,height:14,border:'2px solid white',borderTopColor:'transparent',borderRadius:'50%',animation:'spin .6s linear infinite'}}/> : '▶'}
                {loading ? 'Running...' : 'Ask'}
              </button>
            </div>
          </div>

          {suggestions.length > 0 && !question && (
            <div className="suggestions">
              {suggestions.map((s, i) => (
                <div key={i} className="suggestion-chip" onClick={() => useSuggestion(s)}>
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SQL Editor */}
        {sqlMode && (
          <div className="sql-editor-wrap">
            <textarea
              className="sql-editor"
              rows={4}
              placeholder="SELECT * FROM sales LIMIT 10;"
              value={rawSQL}
              onChange={e => setRawSQL(e.target.value)}
            />
            <div className="sql-run-row">
              <button className="btn-run" onClick={handleRawSQL} disabled={loading || !rawSQL.trim()}>
                ▶ Run SQL
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-bar" onClick={() => dispatch(clearError())}>
            ⚠ {error} <span style={{marginLeft:'auto',cursor:'pointer',opacity:.6}}>×</span>
          </div>
        )}

        {/* Results */}
        <div className="results-area">
          {loading && <LoadingCard />}

          {!loading && !current && !error && (
            <div className="empty-state">
              <div className="empty-icon">◈</div>
              <div className="empty-text">Ask a question to query your database</div>
            </div>
          )}

          {current && !loading && <ResultCard result={current} />}
        </div>
      </main>

      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  )
}

// ── Missing thunk import fix ──────────────────────────────────
import { fetchSuggestions as _fs } from './store/querySlice'

export default function App() {
  return <Provider store={store}><BIApp /></Provider>
}
