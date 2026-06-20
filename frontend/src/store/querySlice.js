import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const runQuery = createAsyncThunk('query/run', async (question, { rejectWithValue }) => {
  try {
    const res = await fetch(`${API}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) {
      const err = await res.json()
      return rejectWithValue(err.detail || 'Query failed')
    }
    return res.json()
  } catch (e) {
    return rejectWithValue('Cannot connect to backend')
  }
})

export const fetchSchema = createAsyncThunk('query/schema', async () => {
  const res = await fetch(`${API}/schema`)
  return res.json()
})

export const fetchSuggestions = createAsyncThunk('query/suggestions', async () => {
  const res = await fetch(`${API}/suggestions`)
  return res.json()
})

export const executeRawSQL = createAsyncThunk('query/raw', async (sql, { rejectWithValue }) => {
  try {
    const res = await fetch(`${API}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql }),
    })
    if (!res.ok) {
      const err = await res.json()
      return rejectWithValue(err.detail || 'SQL failed')
    }
    return res.json()
  } catch (e) {
    return rejectWithValue('Cannot connect to backend')
  }
})

const querySlice = createSlice({
  name: 'query',
  initialState: {
    history:     [],      // [{question, sql, data, chart_type, insight, timestamp}]
    current:     null,
    schema:      null,
    suggestions: [],
    loading:     false,
    error:       null,
    activeTab:   'chat',  // chat | schema | history
    sqlMode:     false,   // toggle raw SQL editor
  },
  reducers: {
    setActiveTab: (s, a) => { s.activeTab = a.payload },
    toggleSQLMode: (s)  => { s.sqlMode = !s.sqlMode },
    clearError:   (s)   => { s.error = null },
    clearCurrent: (s)   => { s.current = null },
  },
  extraReducers: (b) => {
    b
      .addCase(runQuery.pending,   (s) => { s.loading = true; s.error = null })
      .addCase(runQuery.fulfilled, (s, a) => {
        s.loading = false
        s.current = { ...a.payload, timestamp: new Date().toLocaleTimeString() }
        s.history = [s.current, ...s.history].slice(0, 20)
      })
      .addCase(runQuery.rejected,  (s, a) => { s.loading = false; s.error = a.payload })

      .addCase(fetchSchema.fulfilled,      (s, a) => { s.schema = a.payload.schema })
      .addCase(fetchSuggestions.fulfilled, (s, a) => { s.suggestions = a.payload.suggestions || [] })

      .addCase(executeRawSQL.pending,   (s) => { s.loading = true; s.error = null })
      .addCase(executeRawSQL.fulfilled, (s, a) => {
        s.loading = false
        s.current = { sql: 'raw', data: a.payload, chart_type: 'table', insight: '', timestamp: new Date().toLocaleTimeString() }
      })
      .addCase(executeRawSQL.rejected,  (s, a) => { s.loading = false; s.error = a.payload })
  },
})

export const { setActiveTab, toggleSQLMode, clearError, clearCurrent } = querySlice.actions
export default querySlice.reducer
