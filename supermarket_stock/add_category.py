import sqlite3

conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE products
    ADD COLUMN category TEXT DEFAULT 'Other'
""")

conn.commit()
conn.close()

print("Category column added successfully")