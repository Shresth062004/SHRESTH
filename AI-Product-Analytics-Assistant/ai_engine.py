import os
from database import validate_sql

SYSTEM_PROMPT = """You translate business questions into SQLite SELECT queries.
The only table is orders. Use only columns in this schema:
order_id (integer), order_date (text YYYY-MM-DD), customer_id (text),
region (text), customer_segment (text), product_category (text),
product_name (text), quantity (integer), unit_price (real),
discount_pct (real between 0 and 1), payment_method (text),
device_type (text), revenue (real), order_status (text).
Rules:
- Return only one SQLite SELECT query, no markdown and no explanation.
- Never modify data, access external resources, or use other tables.
- Use revenue for sales/revenue metrics.
- Use strftime('%Y-%m', order_date) for monthly grouping.
- For top-N questions, use ORDER BY and LIMIT.
- Avoid SELECT * unless the user explicitly asks to inspect records.
- Keep output to no more than 100 rows.
"""

def _rule_based_sql(question):
    q = question.lower().strip()
    if any(x in q for x in ["highest revenue", "highest sales", "most revenue", "top category", "best category"]):
        return "SELECT product_category, ROUND(SUM(revenue), 2) AS total_revenue FROM orders GROUP BY product_category ORDER BY total_revenue DESC LIMIT 10"
    if "by month" in q or "monthly" in q or "each month" in q:
        return "SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(revenue), 2) AS total_revenue FROM orders GROUP BY month ORDER BY month LIMIT 100"
    if "region" in q and any(x in q for x in ["most", "highest", "orders", "count"]):
        return "SELECT region, COUNT(*) AS order_count FROM orders GROUP BY region ORDER BY order_count DESC LIMIT 10"
    if "average order value" in q or "aov" in q:
        if "payment" in q:
            return "SELECT payment_method, ROUND(AVG(revenue), 2) AS average_order_value FROM orders GROUP BY payment_method ORDER BY average_order_value DESC LIMIT 20"
        return "SELECT ROUND(AVG(revenue), 2) AS average_order_value FROM orders LIMIT 1"
    if "top 5 product" in q or "top five product" in q:
        return "SELECT product_name, ROUND(SUM(revenue), 2) AS total_revenue FROM orders GROUP BY product_name ORDER BY total_revenue DESC LIMIT 5"
    if "customer segment" in q or "segments" in q:
        return "SELECT customer_segment, COUNT(*) AS order_count FROM orders GROUP BY customer_segment ORDER BY order_count DESC LIMIT 20"
    if "compare revenue" in q or "each category" in q or "by category" in q:
        return "SELECT product_category, ROUND(SUM(revenue), 2) AS total_revenue FROM orders GROUP BY product_category ORDER BY total_revenue DESC LIMIT 20"
    if "total revenue" in q and ("number of orders" in q or "count" in q):
        return "SELECT ROUND(SUM(revenue), 2) AS total_revenue, COUNT(*) AS order_count FROM orders LIMIT 1"
    if "total revenue" in q or "total sales" in q:
        return "SELECT ROUND(SUM(revenue), 2) AS total_revenue FROM orders LIMIT 1"
    if "number of orders" in q or "how many orders" in q or "count orders" in q:
        return "SELECT COUNT(*) AS order_count FROM orders LIMIT 1"
    if "payment" in q and "count" in q:
        return "SELECT payment_method, COUNT(*) AS order_count FROM orders GROUP BY payment_method ORDER BY order_count DESC LIMIT 20"
    return None

def _llm_sql(question, schema):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY is not set."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + "\nActual schema:\n" + schema},
                {"role": "user", "content": question}
            ],
            max_tokens=250
        )
        return response.choices[0].message.content.strip(), None
    except Exception as exc:
        return None, f"AI provider request failed: {exc}"

def generate_sql(question, schema):
    sql = _rule_based_sql(question)
    source = "Built-in SQL template"
    if sql is None:
        sql, error = _llm_sql(question, schema)
        source = "LLM API"
        if not sql:
            return None, source, (
                "I couldn't generate SQL. Add OPENAI_API_KEY to your environment to enable AI-generated queries. "
                "You can still try one of the built-in example questions. " + (error or "")
            )
    ok, checked = validate_sql(sql)
    if not ok:
        return None, source, f"Generated query was blocked by safety validation: {checked}"
    return checked, source, None

def explain_result(question, result, sql):
    if result is None or result.empty:
        return "The query returned no rows. Check the filters or ask a broader question."
    if len(result) == 1 and len(result.columns) == 1:
        return f"For your question, the result is **{result.iloc[0, 0]}**."
    numeric = result.select_dtypes(include="number").columns.tolist()
    text_cols = [c for c in result.columns if c not in numeric]
    if len(result) and text_cols and numeric:
        row = result.iloc[0]
        return f"The leading result is **{row[text_cols[0]]}**, with **{row[numeric[0]]}** for **{numeric[0].replace('_', ' ')}**. Review the table for the complete comparison."
    return f"The query returned {len(result)} rows. Review the results table for the values."
