"""
Step 4: Safety + Clarification - Business Data Analyst Agent
Run: python text_to_sql_step4.py
(When you are happy with it, rename it to text_to_sql.py and replace the old file.)

What is new in Step 4, compared with Step 3:
1. Safety: the agent can ONLY read data (SELECT). It will refuse
   DELETE / UPDATE / INSERT / DROP, even if the question asks for it.
2. Clarification: if a question is too vague, the agent asks ONE
   clear question first, instead of guessing the wrong SQL.

Setup is the same as Step 3 - nothing new to install:
- .env in this same folder, with one line: GEMINI_API_KEY=your_key_here
- Model stays gemini-3.5-flash-lite (the stable one from Step 3).
- No need to recreate store.db or .env.
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
- Never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE or TRUNCATE anything.
  This agent only reads data, it never changes the database.
- Use JOINs when you need product or customer names.
- If the question needs a date range, use order_date.
- Keep the query simple and correct.
"""

# Words that would change or delete data - never allowed in the SQL.
BANNED_WORDS = [
    "insert", "update", "delete", "drop", "alter",
    "create", "truncate", "replace", "grant", "revoke",
]

DANGEROUS_REQUEST_WORDS = [
    "delete", "remove", "drop", "update", "change",
    "edit", "insert", "add", "clear", "erase",
]


def is_safe_sql(sql):
    """Step 4 safety check: only ONE SELECT query, nothing dangerous.

    Why this is stricter than Step 3:
    - Step 3 checked 'word in sql', so a harmless word inside another
      word could wrongly block it, and a second statement after a
      semicolon could slip through. This version checks whole words
      and rejects a second statement.
    """
    if not sql or not sql.strip():
        return False
    s = sql.strip()
    # No SQL comments - they can hide a second command.
    if "--" in s or "/*" in s:
        return False
    # Only one statement: remove ONE trailing semicolon, then no
    # semicolon may remain.
    if s.endswith(";"):
        s = s[:-1].strip()
    if ";" in s:
        return False
    # Must start with SELECT (or WITH ... SELECT).
    low = s.lower()
    if low.startswith("with "):
        # WITH must still end in a SELECT for the main query.
        if " select " not in low:
            return False
    elif not low.startswith("select"):
        return False
    # Banned words as whole words only, e.g. "delete" blocks,
    # but a column name containing those letters does not.
    for word in BANNED_WORDS:
        if re.search(r"\b" + word + r"\b", low):
            return False
    return True


def is_dangerous_request(question):
    """True if the user is asking the agent to change or delete data."""
    q = question.lower()
    return any(re.search(r"\b" + word + r"\b", q) for word in DANGEROUS_REQUEST_WORDS)


def needs_clarification(question):
    """Return ONE clarification question, or None if the question is clear.

    Only the vague cases a beginner is likely to type:
    - just one or two words, e.g. 'sales?' or 'best product'
    - 'best' / 'top' with no metric (sold most? most money? most orders?)
    - 'sales' with no period and no product / city / category
    Clear questions such as 'Which product sold most last month?'
    return None and go straight to Gemini.
    """
    q = question.strip().lower()
    words = q.split()
    if len(words) <= 2:
        return "Please tell me a little more - for example, which product, city or time period? Try: 'Which product sold most last month?'"
    if "best" in words and not any(
        w in q for w in ["sold", "sales", "money", "revenue", "quantity", "orders", "spending"]
    ):
        return "When you say 'best', do you mean sold most (quantity) or made the most money (total sales)?"
    if "top" in words and not any(
        w in q for w in ["sold", "sales", "money", "revenue", "quantity", "orders", "spending", "customers", "products", "city", "category"]
    ):
        return "Top by what - most sales, most orders, or most money? And how many, for example top 5?"
    if q in ("show sales", "sales", "show orders", "orders", "show customers", "customers"):
        return "Sales for which period - last month, this month, or last 6 months? And for all products, or one product?"
    return None


def clean_sql(text):
    """Remove markdown code fences if the model adds them."""
    text = text.strip()
    text = re.sub(r"^```sql\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip().rstrip(";") + ";"


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
    # Step 4, part 1 - safety: never even ask Gemini to change data.
    if is_dangerous_request(question):
        print("Blocked: this agent only reads data. It cannot delete, update or change anything in the database.")
        print("Try a reading question instead, for example: 'Which product sold most last month?'")
        return None, None
    # Step 4, part 2 - clarification: ask first, do not guess.
    clarification = needs_clarification(question)
    if clarification:
        print("I need a little more detail before I can answer:")
        print(clarification)
        return None, None
    sql = generate_sql(question)
    print("\nSQL:")
    print(sql)
    df = run_sql(sql)
    print("\nAnswer:")
    print(df.to_string(index=False))
    return sql, df


if __name__ == "__main__":
    print("Business Data Analyst Agent - Step 4 test")
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
