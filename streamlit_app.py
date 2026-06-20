import os
import json
import re
from datetime import date
from typing import TypedDict, Annotated

import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import create_engine, text, inspect
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

load_dotenv()

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="BI Copilot",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg:        #08090c;
    --surface:   #0e1015;
    --raised:    #15171e;
    --raised-2:  #1a1d24;
    --border:    #1f2329;
    --border-hi: #2a2f38;
    --text:      #eceef1;
    --text-dim:  #8b919e;
    --text-faint:#4f545e;
    --amber:     #f5a623;
    --amber-dim: rgba(245,166,35,.12);
    --cyan:      #3ecfdb;
    --cyan-dim:  rgba(62,207,219,.12);
    --red:       #ef5350;
    --green:     #3ddc84;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: var(--bg); }
.block-container { padding: 2.5rem 2.5rem 3rem 2.5rem; max-width: 1180px; }

/* kill default streamlit chrome noise */
#MainMenu, footer, header { visibility: hidden; }

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text) !important;
    letter-spacing: -0.02em !important;
}
p, li, .stMarkdown { color: var(--text-dim); }
code { font-family: 'JetBrains Mono', monospace !important; }

/* ── Hero title block ── */
.bi-hero {
    display: flex; align-items: baseline; gap: 14px;
    margin-bottom: 4px;
}
.bi-hero-mark {
    width: 34px; height: 34px; border-radius: 8px;
    background: linear-gradient(135deg, var(--amber), #c9821a);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Grotesk', sans-serif; font-weight: 700;
    font-size: 16px; color: #08090c; flex-shrink: 0;
    box-shadow: 0 0 0 1px rgba(245,166,35,.3), 0 4px 14px rgba(245,166,35,.18);
}
.bi-hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 30px; font-weight: 700; color: var(--text);
    letter-spacing: -0.03em;
}
.bi-hero-cursor {
    display: inline-block; width: 9px; height: 22px;
    background: var(--amber); margin-left: 6px; vertical-align: -4px;
    animation: blink 1.1s step-end infinite;
}
@keyframes blink { 0%,49% { opacity: 1; } 50%,100% { opacity: 0; } }
.bi-hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px; color: var(--text-faint);
    margin: 6px 0 28px 48px; letter-spacing: .01em;
}

/* ── Section eyebrow labels ── */
.bi-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 500; letter-spacing: .12em;
    text-transform: uppercase; color: var(--text-faint);
    margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.bi-eyebrow::before {
    content: ''; width: 5px; height: 5px; border-radius: 50%;
    background: var(--amber); display: inline-block;
}

/* ── Input ── */
.stTextArea textarea {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 14px 16px !important;
}
.stTextArea textarea::placeholder { color: var(--text-faint) !important; }
.stTextArea textarea:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 3px var(--amber-dim) !important;
}

/* ── Buttons ── */
.stButton button {
    background: var(--amber) !important;
    color: #1a1206 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 10px 22px !important;
    transition: all .12s ease !important;
    box-shadow: 0 1px 0 rgba(255,255,255,.15) inset !important;
}
.stButton button:hover {
    background: #ffb53d !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(245,166,35,.25), 0 1px 0 rgba(255,255,255,.15) inset !important;
}
.stButton button:active { transform: translateY(0); }

/* secondary buttons (sidebar suggestions, history) get quieter style */
section[data-testid="stSidebar"] .stButton button {
    background: var(--raised) !important;
    color: var(--text-dim) !important;
    border: 1px solid var(--border) !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    border-color: var(--amber) !important;
    color: var(--text) !important;
    background: var(--raised-2) !important;
    transform: none;
    box-shadow: none !important;
}

/* download / export buttons quieter too */
.stDownloadButton button {
    background: transparent !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(62,207,219,.3) !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
.stDownloadButton button:hover {
    background: var(--cyan-dim) !important;
    border-color: var(--cyan) !important;
    transform: none;
}

/* ── Toggle ── */
.stToggle label p { color: var(--text-dim) !important; font-size: 13px !important; }

/* ── SQL box ── */
.sql-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 2px solid var(--cyan);
    border-radius: 6px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--cyan);
    margin: 10px 0;
    white-space: pre-wrap;
    line-height: 1.7;
}

/* ── Insight box ── */
.insight-box {
    background: var(--amber-dim);
    border: 1px solid rgba(245,166,35,.25);
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 13.5px;
    color: var(--text);
    margin: 14px 0;
    line-height: 1.65;
}

/* ── Metric card ── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px 20px;
    text-align: center;
}
.metric-value {
    font-size: 42px; font-weight: 700;
    color: var(--amber);
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
}
.metric-label {
    font-size: 11.5px; color: var(--text-faint);
    text-transform: uppercase; letter-spacing: .1em;
    margin-top: 6px; font-family: 'JetBrains Mono', monospace;
}

/* ── Schema panel ── */
.schema-table-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; font-weight: 600;
    color: var(--cyan); margin-bottom: 6px;
}
.schema-col {
    display: flex; justify-content: space-between;
    font-size: 12px; padding: 3px 0;
}
.col-name { color: var(--text); font-family: 'JetBrains Mono', monospace; }
.col-type { color: var(--cyan); font-family: 'JetBrains Mono', monospace; opacity: .7; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

/* radio group styled as nav */
section[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 2px !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent;
    border-radius: 7px;
    padding: 7px 10px !important;
    transition: background .12s;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--raised); }
section[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: var(--text-dim) !important; font-size: 13.5px !important; font-weight: 500 !important;
}

/* ── Headings ── */
h1, h2, h3 { font-weight: 700 !important; }
.stTabs [data-baseweb="tab"] { color: var(--text-faint) !important; font-weight: 500 !important; }
.stTabs [aria-selected="true"] { color: var(--amber) !important; border-bottom-color: var(--amber) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12.5px !important;
    color: var(--text-dim) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }

/* ── Progress bar ── */
.stProgress > div > div { background: var(--amber) !important; }

/* ── Text input (table name etc) ── */
.stTextInput input {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}
.stTextInput input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 3px var(--amber-dim) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {
    background: var(--surface) !important;
    border: 1px dashed var(--border-hi) !important;
    border-radius: 10px !important;
}

/* ── Result header row ── */
.bi-result-q {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px; font-weight: 600; color: var(--text);
}
.bi-result-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px; color: var(--text-faint);
}
.bi-tag {
    display: inline-block; background: var(--raised);
    border: 1px solid var(--border); border-radius: 5px;
    padding: 2px 8px; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--cyan); margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── DB connection ─────────────────────────────────────────────
@st.cache_resource
def get_engine():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        st.error("DATABASE_URL not set in .env or Streamlit secrets")
        st.stop()
    return create_engine(url)

@st.cache_data(ttl=300)
def get_schema_str():
    engine = get_engine()
    inspector = inspect(engine)
    parts = []
    for table in inspector.get_table_names():
        cols = inspector.get_columns(table)
        col_defs = ", ".join(f"{c['name']} {str(c['type'])}" for c in cols)
        try:
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        except Exception:
            count = "?"
        parts.append(f"Table: {table} ({count} rows)\nColumns: {col_defs}")
    return "\n\n".join(parts)

@st.cache_data(ttl=300)
def get_schema_dict():
    engine = get_engine()
    inspector = inspect(engine)
    schema = {}
    for table in inspector.get_table_names():
        cols = inspector.get_columns(table)
        schema[table] = [{"name": c["name"], "type": str(c["type"])} for c in cols]
    return schema

def run_sql(sql: str) -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {"columns": columns, "rows": rows, "count": len(rows)}


# ── CSV upload support ────────────────────────────────────────
def load_csv_as_table(uploaded_file, table_name: str) -> dict:
    """Read uploaded CSV, infer types, write to Postgres as a new table."""
    df = pd.read_csv(uploaded_file)
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name.lower()).strip("_") or "uploaded_data"
    engine = get_engine()
    df.to_sql(safe_name, engine, if_exists="replace", index=False)
    get_schema_str.clear()
    get_schema_dict.clear()
    return {"table_name": safe_name, "rows": len(df), "columns": list(df.columns)}


# ── Groq client ───────────────────────────────────────────────
@st.cache_resource
def get_groq():
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        st.error("GROQ_API_KEY not set")
        st.stop()
    return Groq(api_key=key)

def call_llm(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 1024) -> str:
    client = get_groq()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise SQL and data analysis assistant."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def clean_sql(raw: str) -> str:
    sql = re.sub(r"```sql|```", "", raw).strip()
    sql = re.sub(r"^SQL query:\s*", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"^Validated SQL:\s*", "", sql, flags=re.IGNORECASE).strip()
    return sql

DANGEROUS = re.compile(r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b", re.IGNORECASE)

def is_safe(sql: str) -> bool:
    return not bool(DANGEROUS.search(sql))


# ── LangGraph agents ──────────────────────────────────────────
class AnalystState(TypedDict):
    messages:      Annotated[list, add_messages]
    question:      str
    schema:        str
    raw_sql:       str
    validated_sql: str
    query_result:  dict
    chart_type:    str
    insight:       str
    error:         str

def sql_agent(state: AnalystState) -> AnalystState:
    prompt = f"""
You are an expert SQL analyst. Convert the user's question to a valid PostgreSQL query.

Database schema:
{state['schema']}

User question: {state['question']}

Rules:
- Return ONLY the SQL query, no explanation, no markdown, no backticks
- Always add LIMIT 500 unless aggregating
- Never use DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE

SQL query:
"""
    raw = call_llm(prompt)
    state["raw_sql"] = clean_sql(raw)
    state["error"]   = ""
    return state

def validator_agent(state: AnalystState) -> AnalystState:
    if not is_safe(state.get("raw_sql", "")):
        state["error"] = "Query contains dangerous operations"
        return state
    prompt = f"""
Review and fix this SQL query if needed.
Schema: {state['schema'][:500]}
SQL: {state['raw_sql']}
Return ONLY corrected SQL, no explanation.
"""
    validated = clean_sql(call_llm(prompt))
    state["validated_sql"] = validated if is_safe(validated) else ""
    if not state["validated_sql"]:
        state["error"] = "Query rejected as unsafe"
    return state

def executor_agent(state: AnalystState) -> AnalystState:
    sql = state.get("validated_sql") or state.get("raw_sql", "")
    if not sql or not is_safe(sql):
        state["error"] = "No safe SQL to execute"
        return state
    try:
        state["query_result"] = run_sql(sql)
        state["error"]        = ""
    except Exception as e:
        state["error"]        = f"Query failed: {str(e)}"
        state["query_result"] = {}
    return state

def chart_selector(state: AnalystState) -> AnalystState:
    result = state.get("query_result", {})
    if not result or state.get("error"):
        state["chart_type"] = "table"
        return state
    columns   = result.get("columns", [])
    row_count = result.get("count", 0)
    prompt = f"""
Given SQL: {state.get('validated_sql', '')}
Columns: {', '.join(columns)}
Rows: {row_count}

Return ONLY one word: bar, line, pie, table, or number
"""
    ct = call_llm(prompt, max_tokens=5).strip().lower()
    state["chart_type"] = ct if ct in {"bar","line","pie","table","number"} else "table"
    return state

def insight_node(state: AnalystState) -> AnalystState:
    result = state.get("query_result", {})
    if not result or state.get("error"):
        return state
    rows   = result.get("rows", [])[:10]
    count  = result.get("count", 0)
    prompt = f"""
User asked: {state['question']}
SQL used: {state.get('validated_sql', '')}
Result: {count} rows. Sample: {rows}

Write 2-3 sentences explaining what the data shows and key insights.
Be concise and business-focused.
"""
    state["insight"] = call_llm(prompt, max_tokens=200)
    return state

@st.cache_resource
def build_graph():
    g = StateGraph(AnalystState)
    g.add_node("sql_agent",    sql_agent)
    g.add_node("validator",    validator_agent)
    g.add_node("executor",     executor_agent)
    g.add_node("chart_select", chart_selector)
    g.add_node("insight_node", insight_node)

    g.set_entry_point("sql_agent")
    g.add_edge("sql_agent",    "validator")
    g.add_edge("validator",    "executor")
    g.add_edge("executor",     "chart_select")
    g.add_edge("chart_select", "insight_node")
    g.add_edge("insight_node", END)
    return g.compile()

def run_pipeline(question: str) -> dict:
    graph  = build_graph()
    schema = get_schema_str()
    result = graph.invoke({
        "messages": [], "question": question, "schema": schema,
        "raw_sql": "", "validated_sql": "", "query_result": {},
        "chart_type": "table", "insight": "", "error": "",
    })
    return result


# ── Auto-dashboard generator ──────────────────────────────────
def generate_dashboard_questions(schema: str) -> list[str]:
    """Ask the LLM to propose 4-6 high-value KPI questions for this schema."""
    prompt = f"""
Given this database schema, propose 5 high-value business questions a data analyst
would want answered as KPIs on a dashboard. Mix totals, trends, and breakdowns.

Schema:
{schema}

Return ONLY a JSON array of 5 short question strings, nothing else.
Example: ["Total revenue this year", "Revenue trend by month", "Top 5 products by sales"]
"""
    raw = call_llm(prompt, max_tokens=300)
    try:
        cleaned = re.sub(r"```json|```", "", raw).strip()
        questions = json.loads(cleaned)
        if isinstance(questions, list):
            return questions[:6]
    except Exception:
        pass
    return [
        "Total revenue overall",
        "Revenue trend by month",
        "Top 5 products by revenue",
        "Customer count by segment",
        "Revenue by region",
    ]


# ── Anomaly detection ─────────────────────────────────────────
def detect_anomalies(df: pd.DataFrame, value_col: str, threshold: float = 2.0) -> pd.DataFrame:
    """Flag rows where value_col is >threshold std devs from the mean."""
    if value_col not in df.columns or len(df) < 4:
        return pd.DataFrame()
    mean = df[value_col].mean()
    std  = df[value_col].std()
    if std == 0 or pd.isna(std):
        return pd.DataFrame()
    df = df.copy()
    df["_zscore"] = (df[value_col] - mean) / std
    anomalies = df[df["_zscore"].abs() > threshold].drop(columns=["_zscore"])
    return anomalies


# ── Chart rendering ───────────────────────────────────────────
def render_chart(data: dict, chart_type: str, show_anomalies: bool = False, key: str = None):
    if not data or not data.get("rows"):
        st.warning("No data returned")
        return None

    df = pd.DataFrame(data["rows"])
    if df.empty:
        st.warning("Empty result")
        return None

    num_cols = df.select_dtypes(include="number").columns.tolist()
    str_cols = df.select_dtypes(exclude="number").columns.tolist()
    x_col    = str_cols[0] if str_cols else df.columns[0]
    y_col    = num_cols[0] if num_cols else df.columns[-1]

    COLORS = ["#f5a623","#3ecfdb","#3ddc84","#c9821a","#7dd3dc","#ef5350"]

    chart_key = key or f"chart_{abs(hash(str(data)[:200] + chart_type))}"

    anomalies = pd.DataFrame()
    if show_anomalies and num_cols:
        anomalies = detect_anomalies(df, y_col)

    if chart_type == "number" or (len(df) == 1 and len(df.columns) == 1):
        val = df.iloc[0, 0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val:,.0f if isinstance(val, (int,float)) else val}</div>
            <div class="metric-label">{df.columns[0].replace('_',' ')}</div>
        </div>
        """, unsafe_allow_html=True)
        return df

    if chart_type == "pie" and len(df) <= 10:
        fig = px.pie(df, names=x_col, values=y_col, color_discrete_sequence=COLORS)
        fig.update_layout(paper_bgcolor="#08090c", plot_bgcolor="#08090c", font_color="#eceef1")
        st.plotly_chart(fig, use_container_width=True, key=chart_key)

    elif chart_type == "line":
        fig = px.line(df, x=x_col, y=num_cols if len(num_cols) > 1 else y_col,
                      color_discrete_sequence=COLORS)
        fig.update_layout(paper_bgcolor="#08090c", plot_bgcolor="#0e1015",
                         font_color="#eceef1", xaxis=dict(gridcolor="#1f2329"),
                         yaxis=dict(gridcolor="#1f2329"))
        if not anomalies.empty:
            fig.add_scatter(x=anomalies[x_col], y=anomalies[y_col], mode="markers",
                           marker=dict(color="#ef4444", size=12, symbol="x"),
                           name="Anomaly")
        st.plotly_chart(fig, use_container_width=True, key=chart_key)

    elif chart_type == "bar":
        fig = px.bar(df, x=x_col, y=num_cols if len(num_cols) > 1 else y_col,
                     color_discrete_sequence=COLORS, barmode="group")
        fig.update_layout(paper_bgcolor="#08090c", plot_bgcolor="#0e1015",
                         font_color="#eceef1", xaxis=dict(gridcolor="#1f2329"),
                         yaxis=dict(gridcolor="#1f2329"))
        fig.update_traces(marker_line_width=0)
        if not anomalies.empty:
            fig.add_scatter(x=anomalies[x_col], y=anomalies[y_col], mode="markers",
                           marker=dict(color="#ef4444", size=12, symbol="x"),
                           name="Anomaly")
        st.plotly_chart(fig, use_container_width=True, key=chart_key)

    else:
        st.dataframe(df, use_container_width=True, hide_index=True, key=f"{chart_key}_table")

    if show_anomalies and not anomalies.empty:
        st.markdown(f'<div class="insight-box">⚠ {len(anomalies)} anomaly point(s) detected in <code>{y_col}</code> — flagged in red on the chart above.</div>', unsafe_allow_html=True)
        with st.expander(f"View {len(anomalies)} anomalous row(s)"):
            st.dataframe(anomalies, use_container_width=True, hide_index=True, key=f"{chart_key}_anomalies")

    return df


# ── Session state ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "current" not in st.session_state:
    st.session_state.current = None


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px;">
        <div style="width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,#f5a623,#c9821a);
                    display:flex;align-items:center;justify-content:center;font-family:'Space Grotesk',sans-serif;
                    font-weight:700;font-size:13px;color:#08090c;">◈</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:16px;color:#eceef1;">BI Copilot</div>
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#4f545e;margin:4px 0 18px 36px;">v1.0 · groq + langgraph</div>
    """, unsafe_allow_html=True)
    st.divider()

    tab = st.radio("", ["💬 Chat", "📊 Dashboard", "📁 Upload Data", "🗂 Schema", "📜 History"], label_visibility="collapsed")

    if tab == "🗂 Schema":
        st.markdown('<div class="bi-eyebrow">Database Schema</div>', unsafe_allow_html=True)
        try:
            schema = get_schema_dict()
            for table, cols in schema.items():
                with st.expander(f"⊞ {table} ({len(cols)} cols)"):
                    for c in cols:
                        st.markdown(f"`{c['name']}` — *{c['type'].lower()}*")
        except Exception as e:
            st.error(f"Could not load schema: {e}")

    elif tab == "📜 History":
        st.markdown('<div class="bi-eyebrow">Query History</div>', unsafe_allow_html=True)
        if not st.session_state.history:
            st.caption("No queries yet")
        for i, h in enumerate(st.session_state.history[-10:][::-1]):
            if st.button(f"↩ {h['question'][:40]}...", key=f"h_{i}"):
                st.session_state.current = h
                st.rerun()

    elif tab == "📁 Upload Data":
        st.markdown('<div class="bi-eyebrow">Upload Data</div>', unsafe_allow_html=True)
        st.caption("Upload a CSV — it becomes a queryable table instantly.")
        up_name = st.text_input("Table name", placeholder="my_data")
        up_file = st.file_uploader("CSV file", type=["csv"])
        if up_file and st.button("⬆ Load into database"):
            with st.spinner("Loading CSV into database..."):
                try:
                    info = load_csv_as_table(up_file, up_name or up_file.name.replace(".csv",""))
                    st.success(f"✓ Created table `{info['table_name']}` with {info['rows']} rows, {len(info['columns'])} columns")
                    st.session_state["prefill"] = f"Show me all data from {info['table_name']}"
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    elif tab == "📊 Dashboard":
        st.markdown('<div class="bi-eyebrow">Auto Dashboard</div>', unsafe_allow_html=True)
        st.caption("AI picks 5 KPIs from your schema and builds a dashboard.")
        if st.button("✦ Generate Dashboard", type="primary"):
            st.session_state["build_dashboard"] = True

    else:
        st.markdown('<div class="bi-eyebrow">Try these</div>', unsafe_allow_html=True)
        suggestions = [
            "Show total revenue by region",
            "Top 5 products by units sold",
            "Revenue trend by month",
            "Customer count by country",
            "Which category has highest avg revenue",
        ]
        for s in suggestions:
            if st.button(s, key=f"sug_{s}"):
                st.session_state["prefill"] = s
                st.rerun()


# ── MAIN ─────────────────────────────────────────────────────
st.markdown("""
<div class="bi-hero">
    <div class="bi-hero-mark">◈</div>
    <div class="bi-hero-title">BI Copilot<span class="bi-hero-cursor"></span></div>
</div>
<div class="bi-hero-sub">$ talk to your database in plain english — no SQL required</div>
""", unsafe_allow_html=True)

# ── Auto-dashboard render ───────────────────────────────────
if st.session_state.get("build_dashboard"):
    st.session_state["build_dashboard"] = False
    st.divider()
    st.markdown("## 📊 Auto-Generated Dashboard")

    with st.spinner("Designing your dashboard..."):
        schema = get_schema_str()
        questions = generate_dashboard_questions(schema)

    dash_results = []
    for q in questions:
        with st.spinner(f"Running: {q}"):
            try:
                res = run_pipeline(q)
                if not res.get("error"):
                    dash_results.append({
                        "question":   q,
                        "sql":        res.get("validated_sql") or res.get("raw_sql"),
                        "data":       res.get("query_result", {}),
                        "chart_type": res.get("chart_type", "table"),
                        "insight":    res.get("insight", ""),
                    })
            except Exception:
                continue

    if dash_results:
        for i in range(0, len(dash_results), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(dash_results):
                    item = dash_results[i + j]
                    with col:
                        st.markdown(f"**{item['question']}**")
                        render_chart(item["data"], item["chart_type"], key=f"dash_{i}_{j}")
                        if item.get("insight"):
                            st.caption(item["insight"])
        st.divider()
    else:
        st.warning("Could not generate dashboard — try again.")

# Input
if "prefill" in st.session_state:
    st.session_state["question_input"] = st.session_state.pop("prefill")

question = st.text_area(
    "Ask your database",
    key="question_input",
    placeholder='e.g. "Show me total revenue by region this month"',
    height=80,
    label_visibility="collapsed",
)

col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
with col1:
    ask_btn = st.button("▶ Ask", type="primary", use_container_width=True)
with col2:
    sql_mode = st.toggle("SQL Editor")
with col3:
    show_anomalies = st.toggle("⚠ Anomalies", help="Flag statistical outliers on the chart")

# SQL Editor
if sql_mode:
    raw_sql = st.text_area("Write SQL directly", placeholder="SELECT * FROM sales LIMIT 10;", height=100)
    if st.button("▶ Run SQL"):
        with st.spinner("Executing..."):
            try:
                result = run_sql(raw_sql)
                st.session_state.current = {
                    "question": "Raw SQL",
                    "sql": raw_sql,
                    "data": result,
                    "chart_type": "table",
                    "insight": "",
                }
            except Exception as e:
                st.error(f"SQL Error: {e}")

# Run pipeline
if ask_btn and question.strip():
    with st.spinner("Thinking..."):
        progress = st.progress(0, text="Writing SQL...")
        import time

        progress.progress(25, text="Writing SQL...")
        time.sleep(0.3)
        progress.progress(50, text="Validating query...")
        time.sleep(0.2)

        result = run_pipeline(question.strip())

        progress.progress(75, text="Generating insight...")
        time.sleep(0.2)
        progress.progress(100, text="Done!")
        time.sleep(0.3)
        progress.empty()

        if result.get("error"):
            st.error(f"⚠ {result['error']}")
        else:
            current = {
                "question":   question.strip(),
                "sql":        result.get("validated_sql") or result.get("raw_sql"),
                "data":       result.get("query_result", {}),
                "chart_type": result.get("chart_type", "table"),
                "insight":    result.get("insight", ""),
            }
            st.session_state.current  = current
            st.session_state.history.append(current)

# Display results
if st.session_state.current:
    r = st.session_state.current
    st.divider()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="bi-result-q">{r["question"]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div style="text-align:right;margin-top:6px;">'
            f'<span class="bi-tag">{r["chart_type"]}</span>'
            f'<span class="bi-tag">{r["data"].get("count", 0)} rows</span>'
            f'</div>', unsafe_allow_html=True
        )

    # SQL
    if r.get("sql") and r["sql"] != "Raw SQL":
        with st.expander("🔍 View SQL"):
            st.markdown(f'<div class="sql-box">{r["sql"]}</div>', unsafe_allow_html=True)

    # Chart (+ anomaly detection)
    result_df = render_chart(r["data"], r["chart_type"], show_anomalies=show_anomalies, key=f"main_{len(st.session_state.history)}")

    # Insight
    if r.get("insight"):
        st.markdown(f'<div class="insight-box">✦ {r["insight"]}</div>', unsafe_allow_html=True)

    # Export
    if result_df is not None and not result_df.empty:
        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Export CSV",
            data=csv_bytes,
            file_name=f"query_result_{date.today()}.csv",
            mime="text/csv",
        )
