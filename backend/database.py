import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:pranav123@localhost:5432/analytics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_schema() -> str:
    inspector = inspect(engine)
    schema_parts = []
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        col_defs = ", ".join(f"{c['name']} {str(c['type'])}" for c in columns)
        try:
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        except Exception:
            count = "?"
        schema_parts.append(f"Table: {table_name} ({count} rows)\nColumns: {col_defs}")
    return "\n\n".join(schema_parts)

def get_schema_dict() -> dict:
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [{"name": c["name"], "type": str(c["type"])} for c in columns]
    return schema

def execute_query(sql: str) -> dict:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {"columns": columns, "rows": rows, "count": len(rows)}