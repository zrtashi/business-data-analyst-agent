"""
Step 5: Streamlit UI + Charts - Business Data Analyst Agent
Run: streamlit run app.py
Uses Step 4 safety + clarification from text_to_sql_step4.py.
Same setup as before: .env and store.db in this same folder,
model is gemini-3.5-flash-lite (the stable one from Step 3).
"""
import streamlit as st
import pandas as pd

from text_to_sql_step4 import (
    generate_sql,
    run_sql,
    is_dangerous_request,
    needs_clarification,
)

st.set_page_config(page_title="Business Data Analyst Agent", layout="wide")
st.title("Business Data Analyst Agent")
st.write("Ask your business data in plain English. No SQL needed.")

sample_questions = [
    "Which product sold most last month?",
    "Show sales trend for the last 6 months",
    "What is total sales this month?",
    "Which city buys the most?",
    "Show top 5 customers by total spending",
]

if "question" not in st.session_state:
    st.session_state["question"] = ""

question = st.text_input(
    "Your question:",
    key="question",
    placeholder="Which product sold most last month?",
)

if st.button("Ask"):
    q = question.strip()
    if not q:
        st.warning("Please type a question first.")
    elif is_dangerous_request(q):
        st.error("Blocked: this agent only reads data. It cannot delete, update or change anything in the database.")
        st.info("Try a reading question instead, for example: 'Which product sold most last month?'")
    else:
        clarification = needs_clarification(q)
        if clarification:
            st.warning("I need a little more detail before I can answer:")
            st.info(clarification)
        else:
            try:
                with st.spinner("Calling Gemini, please wait 10-60 seconds..."):
                    sql = generate_sql(q)
                st.subheader("SQL used")
                st.code(sql, language="sql")
                df = run_sql(sql)
                st.subheader("Answer")
                st.dataframe(df, use_container_width=True)
                # Chart: first column is the label, second column is a number.
                if len(df.columns) >= 2 and len(df) > 0 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                    chart_df = df.set_index(df.columns[0])
                    st.subheader("Chart")
                    st.bar_chart(chart_df)
                if len(df) > 0:
                    st.download_button(
                        "Download answer as CSV",
                        df.to_csv(index=False),
                        "answer.csv",
                        "text/csv",
                    )
            except Exception as e:
                st.error(f"Error: {e}")

def set_question(q):
    # Runs as a button callback, before the text box is drawn again,
    # so Streamlit allows changing the text box value here.
    st.session_state["question"] = q


st.subheader("Try a sample question")
for q in sample_questions:
    st.button(q, key=q, on_click=set_question, args=(q,))
