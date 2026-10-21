# AI Product Analytics Assistant

A portfolio project prototype that turns plain-English business questions into SQL-backed answers over a retail orders dataset.

## Features
- Streamlit web interface
- SQLite-backed analytical dataset
- Built-in SQL templates for common questions (works without an API key)
- Optional LLM API for questions outside the templates
- SQL validation: SELECT-only, blocks common write/admin operations, one statement at a time
- Automatic result table and quick bar chart
- Session query history and end-to-end timing
- Basic test set and evaluation script

## Project status
This is a starter prototype. Run it, test it, and improve it before claiming completion or reporting accuracy/latency metrics on a resume. The included dataset is synthetic, not real customer data.

## Setup (Windows / VS Code)
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`
6. Open the local URL shown in the terminal.

Built-in example questions work without an API key.

## Optional LLM support
Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL=gpt-4o-mini` in your terminal environment. Never commit a real API key. API usage may be billed separately from a ChatGPT subscription.

## Dataset
`data/retail_orders.csv` is synthetic and includes order/date, customer, region, segment, category, product, quantity, price, discount, payment method, device type, revenue, and status.

## Evaluation
Run `python tests/evaluate.py`. This is a small smoke test, not a comprehensive AI accuracy benchmark.

## Next improvements
Add more evaluation cases, stronger SQL parsing and execution limits, deployment configuration, and held-out accuracy checks.
