import sqlite3

conn = sqlite3.connect("supermarket.db")
cursor = conn.cursor()

# Rice
cursor.execute("""
    UPDATE products
    SET category = 'Groceries'
    WHERE LOWER(name) = 'rice'
""")

# Milk
cursor.execute("""
    UPDATE products
    SET category = 'Dairy'
    WHERE LOWER(name) = 'milk'
""")

# Biscuits
cursor.execute("""
    UPDATE products
    SET category = 'Snacks'
    WHERE LOWER(name) LIKE '%biscuit%'
""")

# Sugar
cursor.execute("""
    UPDATE products
    SET category = 'Groceries'
    WHERE LOWER(name) = 'sugar'
""")

# Any other products
cursor.execute("""
    UPDATE products
    SET category = 'Other'
    WHERE category IS NULL
       OR category = ''
""")

conn.commit()

print("Categories updated successfully!")

cursor.execute("""
    SELECT id, name, category
    FROM products
    ORDER BY id
""")

products = cursor.fetchall()

print("\nCurrent Products:")
print("------------------------------")

for product in products:
    print(
        f"ID: {product[0]} | "
        f"Name: {product[1]} | "
        f"Category: {product[2]}"
    )

conn.close()