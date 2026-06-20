# ◈ BI Copilot

AI-powered business intelligence assistant that lets you talk to your database in plain English. Built on a LangGraph multi-agent pipeline — ask a question, get SQL, a chart, and an AI-written insight, all in one flow.

**Live demo:** _add your Streamlit Cloud URL here once deployed_

![BI Copilot demo](demo.png)

---

## What it does

Type a question like *"show me total revenue by region"* and BI Copilot:

1. Writes the SQL query for you
2. Validates it's safe (read-only, schema-aware)
3. Runs it against your PostgreSQL database
4. Picks the best chart type automatically (bar / line / pie / table / number)
5. Explains the result in plain English

No SQL knowledge required.

---

## Features

- **Natural language to SQL** — ask questions, get charts, not query syntax
- **Auto-generated dashboards** — one click, AI proposes 5 relevant KPIs from your schema and builds a full dashboard
- **Bring your own data** — upload any CSV, it becomes a queryable table instantly
- **Anomaly detection** — flags statistical outliers on trend charts automatically
- **Export results** — download any query result as CSV
- **SQL editor mode** — for power users who want to write raw SQL directly
- **Query history** — revisit and re-run past questions with one click
- **Schema explorer** — browse all tables and columns in the sidebar

---

## Tech Stack

| Layer | Technology |
|---|---|
| App framework | Streamlit |
| AI agent framework | LangGraph (5-node pipeline) |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Database | PostgreSQL |
| Charts | Plotly |
| Data handling | Pandas |

---

## LangGraph Pipeline

```
question → sql_agent → validator → executor → chart_selector → insight_node
```

| Node | Responsibility |
|---|---|
| `sql_agent` | Converts natural language question to SQL using schema context |
| `validator` | Checks for destructive operations, fixes syntax issues |
| `executor` | Runs the validated query against PostgreSQL |
| `chart_select` | Picks the most appropriate visualization type |
| `insight_node` | Generates a plain-English explanation of the results |

Every query is blocked from destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`) at two layers — the validator agent and a regex safety check before execution.

---

## Project Structure

```
bi-copilot/
├── streamlit_app.py          # Main app — UI, agents, all logic
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example  # Template for API keys
├── backend/                  # Standalone FastAPI + React version (reference)
│   ├── main.py
│   ├── agents.py
│   ├── database.py
│   ├── prompts.py
│   └── seed.py
└── frontend/                 # React + Redux UI (reference)
    └── src/...
```

> The project also includes a full FastAPI + React/Redux implementation under `backend/` and `frontend/` for reference — the Streamlit app in the root is the primary, deployed version.

---

## Setup & Running Locally

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (or a free [Neon](https://neon.tech) database)
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Installation

```bash
git clone https://github.com/asanepranav/bi-copilot.git
cd bi-copilot

python -m venv venv
venv\Scripts\activate.bat      # Windows
source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
```

### Configure secrets

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_groq_key_here"
DATABASE_URL = "postgresql+psycopg://postgres:yourpassword@localhost:5432/analytics"
```

### Seed sample data (optional)

```bash
cd backend
python seed.py
cd ..
```

Creates `sales`, `customers`, and `products` tables with 1000+ realistic records.

### Run

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`

---

## Example Questions to Try

```
Show me total revenue by region
Top 5 products by units sold
Revenue trend by month
Which category has the highest average revenue
How many customers joined each month
```

---

## Deployment

Deployed on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push repo to GitHub
2. Connect repo on Streamlit Cloud, set main file to `streamlit_app.py`
3. Add `GROQ_API_KEY` and `DATABASE_URL` under **App settings → Secrets**
4. Deploy

For the production database, this project uses a free [Neon](https://neon.tech) PostgreSQL instance since Streamlit Cloud cannot reach a local database.

---

## Author

**Pranav Asane**
[GitHub](https://github.com/asanepranav) · [LinkedIn](https://linkedin.com/in/pranav-asane)
