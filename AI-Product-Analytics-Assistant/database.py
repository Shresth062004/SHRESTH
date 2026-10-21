from pathlib import Path
import re
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "retail_orders.csv"
DB_PATH = ROOT / "data" / "retail_orders.db"

def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)

def initialize_database():
    df = load_data()
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("orders", conn, if_exists="replace", index=False)
    return len(df)

def get_schema():
    df = load_data()
    lines = ["Table: orders", "Columns:"]
    for col in df.columns:
        lines.append(f"- {col} ({df[col].dtype})")
    lines.append("Note: order_date is stored as YYYY-MM-DD text.")
    return "\n".join(lines)

def validate_sql(sql):
    if not isinstance(sql, str) or not sql.strip():
        return False, "No SQL query was provided."
    cleaned = sql.strip()
    cleaned = re.sub(r"^\x60\x60\x60(?:sql)?\s*|\s*\x60\x60\x60$", "", cleaned, flags=re.IGNORECASE).strip()
    if ";" in cleaned.rstrip(";"):
        return False, "Only one SQL statement is allowed."
    cleaned = cleaned.rstrip(";").strip()
    if not re.match(r"(?is)^select\b", cleaned):
        return False, "Only SELECT queries are allowed."
    forbidden = r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex|grant|revoke|exec|execute)\b"
    if re.search(forbidden, cleaned, flags=re.IGNORECASE):
        return False, "The query contains a blocked SQL operation."
    if re.search(r"\b(load_extension|readfile|writefile)\s*\(", cleaned, flags=re.IGNORECASE):
        return False, "The query contains a blocked SQLite function."
    return True, cleaned

def run_read_only_query(sql):
    ok, cleaned_or_error = validate_sql(sql)
    if not ok:
        return pd.DataFrame(), cleaned_or_error
    cleaned = cleaned_or_error
    if not re.search(r"\blimit\s+\d+\b", cleaned, flags=re.IGNORECASE):
        cleaned += " LIMIT 100"
    try:
        df = load_data()
        conn = sqlite3.connect(":memory:")
        df.to_sql("orders", conn, if_exists="replace", index=False)
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.execute(cleaned)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        return pd.DataFrame(rows, columns=cols), None
    except Exception as exc:
        return pd.DataFrame(), f"Query could not be executed: {exc}"

def get_sample_questions():
    return [
        "Which product category has the highest revenue?",
        "What is the total revenue by month?",
        "Which region has the most orders?",
        "What is the average order value by payment method?",
        "Show the top 5 products by revenue.",
        "How many orders are there in each customer segment?",
        "Compare revenue for each category.",
        "What is the total revenue and number of orders?"
    ]
