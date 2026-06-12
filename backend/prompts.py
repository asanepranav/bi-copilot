SQL_AGENT_PROMPT = """
You are an expert SQL analyst. Convert the user's question to a valid PostgreSQL query.

Database schema:
{schema}

User question: {question}

Rules:
- Return ONLY the SQL query, no explanation, no markdown, no backticks
- Use only tables and columns that exist in the schema above
- Always add LIMIT 500 unless user asks for aggregations
- Use proper PostgreSQL syntax
- For date filters use: WHERE date_column >= NOW() - INTERVAL '30 days'
- Never use DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE
- If the question is unclear, write the most reasonable query

SQL query:
"""

VALIDATOR_PROMPT = """
You are a SQL safety validator. Review this SQL query and fix any issues.

Database schema:
{schema}

Original SQL: {sql}

Check for:
1. Safety: No destructive operations (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE)
2. Validity: All tables and columns exist in schema
3. Performance: Add LIMIT if missing and query is not an aggregation
4. Correctness: Fix syntax errors

Return ONLY the corrected SQL query. If the original is fine, return it as-is.
No explanation, no markdown, no backticks.

Validated SQL:
"""

INSIGHT_PROMPT = """
You are a data analyst. The user asked a question and we ran a SQL query. Explain the results.

User question: {question}
SQL query used: {sql}
Result summary: {summary}

Write 2-3 sentences explaining:
- What the data shows
- Any notable patterns or insights
- What action the user might take

Keep it concise and business-focused. No technical jargon.
"""

CHART_TYPE_PROMPT = """
Given this SQL query and result columns, suggest the best chart type.

SQL: {sql}
Columns: {columns}
Row count: {row_count}

Return ONLY one of: bar, line, pie, table, number

Rules:
- bar: comparisons between categories (e.g. sales by region)
- line: trends over time (e.g. revenue by month)
- pie: part-of-whole with <8 categories (e.g. market share)
- number: single value result (COUNT, SUM returning 1 row)
- table: complex multi-column data or >20 rows

Chart type:
"""
