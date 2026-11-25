# Business Data Analyst Agent

Ask your business data in plain English. No SQL needed.

Type a question like "Which product sold most last month?" and the agent turns it into SQL, runs it safely on a SQLite database, and shows the answer as a table and a chart, with a CSV download.

## Live demo

Deployed on Streamlit Community Cloud (free). Add the live link here after deploying.

## What it does

- Text-to-SQL with Google Gemini (`gemini-3.5-flash-lite`)
- Safety first: only `SELECT` queries are allowed. DELETE, UPDATE, INSERT, DROP and similar requests are blocked before any AI call.
- Clarification: if a question is too vague (for example, just "best product"), the agent asks one clear question instead of guessing.
- Streamlit UI with tables, bar charts and CSV download.
- Sample online-store data: 10 products, 60 customers, 850 orders.

## Tested — 10 out of 10 questions pass

1. Which product sold most last month? — Laptop Stand
2. Show sales trend for the last 6 months — monthly table + bar chart
3. Which customers stopped buying in the last 90 days? — Hassan Ali, Omar Khan, Rabia Ali, Hassan Khan
4. What is total sales this month? — 4303.93
5. Which city buys the most? — Multan
6. Which category makes the most money? — Electronics
7. Show top 5 customers by total spending
8. Which products are low selling?
9. How many orders were there last week? — 14
10. What is the average order value? — 88.86

## Run it locally

```bash
pip install -r requirements.txt
```

Create a `.env` file in this folder with your free Gemini API key (get one at https://aistudio.google.com/):

```
GEMINI_API_KEY=your_key_here
```

Then run:

```bash
streamlit run app.py
```

The app opens at http://localhost:8501

## Deploy on Streamlit Cloud

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io/ and create a new app from this repo, main file `app.py`.
3. In the app settings, add a Secret (do not commit it to GitHub):

```
GEMINI_API_KEY=your_key_here
```

Never commit `.env` to GitHub. It is listed in `.gitignore`.

## Files

- `app.py` — Streamlit UI (Step 5)
- `text_to_sql_step4.py` — Text-to-SQL with safety + clarification (Step 4)
- `text_to_sql.py` — Step 3 command-line version
- `create_sample_data.py` — creates `store.db` with sample data (Step 2)
- `store.db` — sample SQLite database
- `requirements.txt` — Python packages
- `test_questions.md` — the 10 test questions (Step 6)

## Tech

Python, SQLite, Streamlit, Google Gemini API (`google-genai`).
