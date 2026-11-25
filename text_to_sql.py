"""
Step 3: Basic Text-to-SQL - FIXED version
Run: python text_to_sql.py
Uses the new google-genai package and gemini-3.5-flash-lite.
The old google-generativeai package and gemini-2.5-flash no longer work for new users.

Setup first:
1. Get a FREE Gemini API key from https://aistudio.google.com/
2. In this same folder, create a file named .env with one line:
   GEMINI_API_KEY=your_key_here
   Never share this key. Do not put it in chat.
3. Install packages (with (agent) active):
   pip install google-genai pandas python-dotenv
   If you installed the old package before, also run:
   pip uninstall -y google-generativeai
"""
import os
import re
import sqlite3

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

SCHEMA = """
products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL)
customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT, signup_date TEXT)
orders(id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, quantity INTEGER, order_date TEXT, total_amount REAL)

Relationships:
- orders.customer_id -> customers.id
- orders.product_id -> products.id
- order_date is YYYY-MM-DD
- total_amount = price * quantity for that order
- Today is 2026-11-23. "last month" means 2026-10-23 to 2026-11-23 unless the user says otherwise.
"""

SYSTEM_PROMPT = f"""You are a Text-to-SQL assistant for a small online store.
Database schema:
{SCHEMA}

Rules:
- Return ONLY one SQL SELECT query. No explanation, no markdown, no extra text.
- Only use tables and columns from the schema above.
- Use JOINs when you need product or customer names.
- If the question needs a date range, use order_date.
- Keep the query simple and correct.
"""


def clean_sql(text):
    """Remove markdown code fences if the model adds them."""
    text = text.strip()
    text = re.sub(r"^```sql\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip().rstrip(";") + ";"


def is_safe_sql(sql):
    """Step 4 safety check, used here too: only SELECT, nothing dangerous."""
    s = sql.strip().lower()
    if not s.startswith("select"):
        return False
    banned = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
    return not any(word in s for word in banned)


def generate_sql(question):
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file. Please add it first.")

    client = genai.Client(api_key=api_key)
    # Progress print: without this, the screen just blinks while Gemini
    # answers (first call can take 30-60 seconds) and looks frozen.
    print("Calling Gemini, please wait 10-60 seconds...", flush=True)
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=SYSTEM_PROMPT + "\nQuestion: " + question,
    )
    print("Gemini replied.", flush=True)
    return clean_sql(response.text)


def run_sql(sql):
    if not is_safe_sql(sql):
        raise ValueError("Unsafe SQL blocked. Only SELECT queries are allowed.")
    conn = sqlite3.connect("store.db")
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def ask(question):
    sql = generate_sql(question)
    print("\nSQL:")
    print(sql)
    df = run_sql(sql)
    print("\nAnswer:")
    print(df.to_string(index=False))
    return sql, df


if __name__ == "__main__":
    print("Business Data Analyst Agent - Step 3 test")
    print("Type a question, or press Enter to use the sample question.")
    print("Type 'exit' to quit.\n")
    while True:
        q = input("Your question: ").strip()
        if q.lower() == "exit":
            break
        if not q:
            q = "Which product sold most last month?"
            print("Using sample question:", q)
        try:
            ask(q)
        except Exception as e:
            print("Error:", e)
        print("\n---\n")
