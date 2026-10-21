import streamlit as st
import pandas as pd
import time
from database import load_data, get_schema, run_read_only_query, get_sample_questions
from ai_engine import generate_sql, explain_result

st.set_page_config(page_title="AI Product Analytics Assistant", page_icon="📊", layout="wide")
st.title("📊 AI Product Analytics Assistant")
st.caption("Ask business questions in plain English and explore answers backed by SQL.")

with st.sidebar:
    st.header("About this project")
    st.write("A portfolio prototype that converts business questions into read-only SQL, executes queries against a sample retail dataset, and summarizes results.")
    st.markdown("**Safety controls**")
    st.write("- Read-only SELECT queries only")
    st.write("- Single query per request")
    st.write("- Query timeout and row limit")
    st.write("- AI output is validated before execution")
    st.divider()
    st.caption("Demo dataset: synthetic retail orders. Replace it with your own authorized dataset when ready.")

@st.cache_data
def get_data():
    return load_data()

df = get_data()
schema = get_schema()
with st.expander("View dataset and schema"):
    st.write(f"Rows: **{len(df):,}** · Columns: **{len(df.columns)}**")
    st.code(schema)
    st.dataframe(df.head(20), use_container_width=True)

st.subheader("Ask a question")
examples = get_sample_questions()
chosen = st.selectbox("Try an example", ["Choose an example..."] + examples)
default_question = "" if chosen == "Choose an example..." else chosen
question = st.text_input("Business question", value=default_question, placeholder="e.g. Which product category has the highest revenue?")
run = st.button("Analyze", type="primary", disabled=not bool(question.strip()))

if run:
    started = time.perf_counter()
    with st.spinner("Generating and validating SQL..."):
        sql, source, note = generate_sql(question, schema)
    if not sql:
        st.error(note or "Could not generate a safe SQL query.")
        st.stop()
    st.markdown("### Generated SQL")
    st.code(sql, language="sql")
    with st.spinner("Running query..."):
        result, error = run_read_only_query(sql)
    elapsed = time.perf_counter() - started
    if error:
        st.error(error)
        st.info("Try asking a simpler question or inspect the dataset schema.")
        st.stop()
    st.markdown("### Results")
    st.caption(f"Source: {source} · End-to-end time: {elapsed:.2f} seconds · Returned rows: {len(result)}")
    if result.empty:
        st.warning("The query ran successfully but returned no rows.")
    else:
        st.dataframe(result, use_container_width=True)
        numeric_cols = result.select_dtypes(include="number").columns.tolist()
        if len(result.columns) >= 2 and numeric_cols:
            category_col = next((c for c in result.columns if c not in numeric_cols), result.columns[0])
            metric_col = numeric_cols[0]
            try:
                st.markdown("### Quick chart")
                st.bar_chart(result.set_index(category_col)[metric_col])
            except Exception:
                pass
    st.markdown("### Plain-English summary")
    st.write(explain_result(question, result, sql))
    st.session_state.setdefault("history", [])
    st.session_state["history"].insert(0, {"question": question, "sql": sql, "rows": len(result), "seconds": round(elapsed, 3), "source": source})
    st.markdown("### Evaluation note")
    st.write("This run records execution and response time, but it does not by itself prove answer accuracy. Use the evaluation script with known expected results before reporting accuracy on a resume.")

if "history" in st.session_state and st.session_state["history"]:
    st.divider()
    st.subheader("This session's query history")
    st.dataframe(pd.DataFrame(st.session_state["history"]), use_container_width=True)
