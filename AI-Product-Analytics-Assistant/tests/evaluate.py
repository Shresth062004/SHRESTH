import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import run_read_only_query, get_schema
from ai_engine import generate_sql

CASES = [
    {"question": "Which product category has the highest revenue?", "expected_sql_contains": "GROUP BY product_category", "expected_columns": ["product_category", "total_revenue"]},
    {"question": "What is the total revenue by month?", "expected_sql_contains": "strftime", "expected_columns": ["month", "total_revenue"]},
    {"question": "Which region has the most orders?", "expected_sql_contains": "GROUP BY region", "expected_columns": ["region", "order_count"]},
    {"question": "Show the top 5 products by revenue.", "expected_sql_contains": "LIMIT 5", "expected_columns": ["product_name", "total_revenue"]},
    {"question": "How many orders are there in each customer segment?", "expected_sql_contains": "GROUP BY customer_segment", "expected_columns": ["customer_segment", "order_count"]}
]

def main():
    passed = 0
    for case in CASES:
        sql, source, note = generate_sql(case["question"], get_schema())
        if not sql:
            print(f"FAIL | {case['question']} | {note}")
            continue
        result, error = run_read_only_query(sql)
        checks = error is None and case["expected_sql_contains"].lower() in sql.lower() and all(col in result.columns for col in case["expected_columns"])
        if checks:
            passed += 1
            print(f"PASS | {case['question']} | {source} | {len(result)} rows")
        else:
            print(f"FAIL | {case['question']} | SQL={sql!r} | error={error!r} | columns={list(result.columns)}")
    print(f"\nSmoke-test result: {passed}/{len(CASES)} passed")
    if passed != len(CASES):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
