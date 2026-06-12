import os, re
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from groq import Groq

from database import get_schema, execute_query
from prompts import SQL_AGENT_PROMPT, VALIDATOR_PROMPT, INSIGHT_PROMPT, CHART_TYPE_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a precise SQL and data analysis assistant. Follow instructions exactly."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def clean_sql(raw: str) -> str:
    """Strip markdown, backticks, leading/trailing whitespace."""
    sql = re.sub(r"```sql|```", "", raw).strip()
    sql = re.sub(r"^SQL query:\s*", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"^Validated SQL:\s*", "", sql, flags=re.IGNORECASE).strip()
    return sql

DANGEROUS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b",
    re.IGNORECASE
)

def is_safe(sql: str) -> bool:
    return not bool(DANGEROUS.search(sql))


# ── Shared state ──────────────────────────────────────────────
class AnalystState(TypedDict):
    messages:     Annotated[list, add_messages]
    question:     str
    schema:       str
    raw_sql:      str
    validated_sql: str
    query_result: dict
    chart_type:   str
    insight:      str
    error:        str


# ── Node 1: SQL agent → NL to SQL ────────────────────────────
def sql_agent(state: AnalystState) -> AnalystState:
    schema   = state.get("schema") or get_schema()
    prompt   = SQL_AGENT_PROMPT.format(schema=schema, question=state["question"])
    raw      = call_llm(prompt)
    state["raw_sql"] = clean_sql(raw)
    state["schema"]  = schema
    state["error"]   = ""
    return state


# ── Node 2: Validator → check + fix SQL ──────────────────────
def validator_agent(state: AnalystState) -> AnalystState:
    if not state.get("raw_sql"):
        state["error"] = "No SQL generated"
        return state

    if not is_safe(state["raw_sql"]):
        state["error"]         = "Query contains dangerous operations"
        state["validated_sql"] = ""
        return state

    prompt = VALIDATOR_PROMPT.format(
        schema=state["schema"],
        sql=state["raw_sql"],
    )
    validated        = clean_sql(call_llm(prompt))
    state["validated_sql"] = validated if is_safe(validated) else ""

    if not state["validated_sql"]:
        state["error"] = "Validator rejected the query as unsafe"
    return state


# ── Node 3: Executor → run SQL on DB ─────────────────────────
def executor_agent(state: AnalystState) -> AnalystState:
    sql = state.get("validated_sql") or state.get("raw_sql", "")

    if not sql:
        state["error"] = "No valid SQL to execute"
        return state

    if not is_safe(sql):
        state["error"] = "Query blocked: contains dangerous operations"
        return state

    try:
        result             = execute_query(sql)
        state["query_result"] = result
        state["error"]        = ""
    except Exception as e:
        state["error"]        = f"Query execution failed: {str(e)}"
        state["query_result"] = {}

    return state


# ── Node 4: Chart type selector ───────────────────────────────
def chart_selector(state: AnalystState) -> AnalystState:
    result = state.get("query_result", {})
    if not result or state.get("error"):
        state["chart_type"] = "table"
        return state

    columns   = result.get("columns", [])
    row_count = result.get("count", 0)
    sql       = state.get("validated_sql", "")

    prompt = CHART_TYPE_PROMPT.format(
        sql=sql,
        columns=", ".join(columns),
        row_count=row_count,
    )
    chart_type = call_llm(prompt, max_tokens=10).strip().lower()

    valid_types       = {"bar", "line", "pie", "table", "number"}
    state["chart_type"] = chart_type if chart_type in valid_types else "table"
    return state


# ── Node 5: Insight agent → explain results ──────────────────
def insight_agent(state: AnalystState) -> AnalystState:
    result = state.get("query_result", {})
    if not result or state.get("error"):
        state["insight"] = ""
        return state

    rows      = result.get("rows", [])
    row_count = result.get("count", 0)

    # build summary for LLM (cap at 10 rows to save tokens)
    sample    = rows[:10]
    summary   = f"{row_count} rows returned. Sample: {sample}"

    prompt = INSIGHT_PROMPT.format(
        question=state["question"],
        sql=state.get("validated_sql", ""),
        summary=summary,
    )
    state["insight"] = call_llm(prompt, max_tokens=256)
    return state


# ── Build graph ───────────────────────────────────────────────
def build_graph():
    g = StateGraph(AnalystState)

    g.add_node("sql_agent",    sql_agent)
    g.add_node("validator",    validator_agent)
    g.add_node("executor",     executor_agent)
    g.add_node("chart_select", chart_selector)
    g.add_node("insight_node", insight_agent)

    g.set_entry_point("sql_agent")
    g.add_edge("sql_agent",    "validator")
    g.add_edge("validator",    "executor")
    g.add_edge("executor",     "chart_select")
    g.add_edge("chart_select", "insight_node")
    g.add_edge("insight_node", END)

    return g.compile()

graph = build_graph()
