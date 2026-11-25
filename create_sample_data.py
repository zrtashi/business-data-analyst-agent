"""
Step 2: Create sample business data
Run: python create_sample_data.py
Creates store.db in the same folder.
Tables: products, customers, orders
Sample online store, 12 months of orders.
No real client data - demo only.
"""
import sqlite3
import random
from datetime import date, timedelta

random.seed(42)

DB = "store.db"

products = [
    (1, "Wireless Headphones", "Electronics", 49.99),
    (2, "Smart Watch", "Electronics", 89.99),
    (3, "Laptop Stand", "Accessories", 29.99),
    (4, "Bluetooth Speaker", "Electronics", 39.99),
    (5, "Phone Case", "Accessories", 14.99),
    (6, "Running Shoes", "Fashion", 59.99),
    (7, "Backpack", "Fashion", 44.99),
    (8, "Coffee Maker", "Home", 69.99),
    (9, "Desk Lamp", "Home", 24.99),
    (10, "Yoga Mat", "Fitness", 19.99),
]

cities = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan"]
first_names = ["Ali", "Sara", "Ahmed", "Fatima", "Usman", "Ayesha", "Bilal", "Hina", "Omar", "Zainab", "Hassan", "Maryam", "Danish", "Noor", "Imran", "Sana", "Fahad", "Rabia", "Tariq", "Mehwish"]

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("DROP TABLE IF EXISTS customers")
cur.execute("DROP TABLE IF EXISTS products")

cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL)")
cur.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT, signup_date TEXT)")
cur.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, quantity INTEGER, order_date TEXT, total_amount REAL)")

cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

customers = []
start_signup = date(2025, 1, 1)
for i in range(1, 61):
    name = f"{random.choice(first_names)} {random.choice(['Khan', 'Ahmed', 'Ali', 'Malik', 'Raza', 'Hussain'])}"
    city = random.choice(cities)
    signup = start_signup + timedelta(days=random.randint(0, 330))
    customers.append((i, name, city, signup.isoformat()))

cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

# Orders: Nov 2025 to Nov 2026 approx, weighted to recent months
orders = []
order_id = 1
start = date(2025, 11, 23)
end = date(2026, 11, 23)
days = (end - start).days
for _ in range(850):
    order_date = start + timedelta(days=random.randint(0, days))
    customer_id = random.randint(1, 60)
    product_id, _, _, price = random.choice(products)
    quantity = random.randint(1, 3)
    total = round(price * quantity, 2)
    orders.append((order_id, customer_id, product_id, quantity, order_date.isoformat(), total))
    order_id += 1

cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders)
conn.commit()

# Quick checks
for table in ["products", "customers", "orders"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(table, cur.fetchone()[0])

cur.execute("SELECT MIN(order_date), MAX(order_date), ROUND(SUM(total_amount),2) FROM orders")
print("orders range and total sales:", cur.fetchone())
conn.close()
print("Done: store.db created")
