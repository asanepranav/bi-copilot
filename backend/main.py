import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from database import get_schema, get_schema_dict, execute_query
from agents import graph

load_dotenv()

app = FastAPI(title="BI Copilot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cache schema on startup (avoids repeated introspection) ──
_schema_cache = None

def get_cached_schema():
    global _schema_cache
    if not _schema_cache:
        _schema_cache = get_schema()
    return _schema_cache


# ── Schemas ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    refresh_schema: Optional[bool] = False

class RawSQLRequest(BaseModel):
    sql: str


# ── Health ────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Schema endpoint ───────────────────────────────────────────
@app.get("/schema")
def get_db_schema():
    """Return DB schema for frontend display."""
    try:
        return {"schema": get_schema_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema fetch failed: {str(e)}")


# ── Main query endpoint ───────────────────────────────────────
@app.post("/query")
def run_query(payload: QueryRequest):
    """
    Full pipeline: NL question → SQL → validate → execute → chart type → insight
    """
    global _schema_cache
    if payload.refresh_schema:
        _schema_cache = None

    schema = get_cached_schema()

    try:
        result = graph.invoke({
            "messages":      [],
            "question":      payload.question,
            "schema":        schema,
            "raw_sql":       "",
            "validated_sql": "",
            "query_result":  {},
            "chart_type":    "table",
            "insight":       "",
            "error":         "",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return {
        "question":     payload.question,
        "sql":          result.get("validated_sql") or result.get("raw_sql"),
        "data":         result.get("query_result", {}),
        "chart_type":   result.get("chart_type", "table"),
        "insight":      result.get("insight", ""),
    }


# ── Raw SQL execution (for power users) ──────────────────────
@app.post("/execute")
def execute_raw(payload: RawSQLRequest):
    """Execute SQL directly — for power users / SQL editor."""
    dangerous = ["drop","delete","update","insert","alter","create","truncate"]
    sql_lower = payload.sql.lower()
    if any(kw in sql_lower for kw in dangerous):
        raise HTTPException(status_code=403, detail="Dangerous SQL blocked")
    try:
        result = execute_query(payload.sql)
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


# ── Sample questions for UI ───────────────────────────────────
@app.get("/suggestions")
def get_suggestions():
    """Return schema-aware example questions."""
    try:
        schema = get_schema_dict()
        tables = list(schema.keys())
        suggestions = [
            f"Show me all records from {tables[0]}" if tables else "Show me all tables",
            f"How many rows are in {tables[0]}?" if tables else "Count all rows",
            f"What are the top 10 records by the first numeric column in {tables[0]}?" if tables else "Show top 10",
            "Show me data from the last 30 days",
            "What is the total count grouped by category?",
        ]
        return {"suggestions": suggestions, "tables": tables}
    except Exception:
        return {"suggestions": ["Show me all data", "Count rows by category"], "tables": []}
