from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "instantthings_secret_key"

DATABASE = "supermarket.db"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    return sqlite3.connect(DATABASE)


# =====================================================
# CREATE DATABASE
# =====================================================

def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT,
            category TEXT DEFAULT 'Other'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            sale_date TEXT NOT NULL
        )
    """)

    # Check existing columns
    cursor.execute("PRAGMA table_info(products)")

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    # Add image column if missing
    if "image" not in columns:

        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN image TEXT
        """)

    # Add category column if missing
    if "category" not in columns:

        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN category TEXT DEFAULT 'Other'
        """)

    # Sample products
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    count = cursor.fetchone()[0]

    if count == 0:

        products = [
            ("Rice", 60, 20, None, "Groceries"),
            ("Milk", 30, 5, None, "Dairy"),
            ("Biscuits", 20, 0, None, "Snacks"),
            ("Sugar", 50, 10, None, "Groceries")
        ]

        cursor.executemany("""
            INSERT INTO products
            (name, price, stock, image, category)
            VALUES (?, ?, ?, ?, ?)
        """, products)

    # Fix empty categories
    cursor.execute("""
        UPDATE products
        SET category = 'Other'
        WHERE category IS NULL
        OR category = ''
    """)

    conn.commit()
    conn.close()


# =====================================================
# ADMIN CHECK
# =====================================================

def admin_required():

    return session.get("admin") is True


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template("index.html")


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin"):

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == "admin"
            and password == "admin123"
        ):

            session["admin"] = True

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect(
        url_for("login")
    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if not admin_required():

        return redirect(
            url_for("login")
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE stock > 5
    """)

    available = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE stock > 0
        AND stock <= 5
    """)

    low_stock = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE stock = 0
    """)

    out_of_stock = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(price), 0)
        FROM sales
    """)

    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
    """)

    total_transactions = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        available=available,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        total_sales=total_sales,
        total_transactions=total_transactions
    )


# =====================================================
# PRODUCTS
# =====================================================

@app.route("/products")
def product_list():

    if not admin_required():

        return redirect(
            url_for("login")
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, stock, image, category
        FROM products
        ORDER BY id
    """)

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:

        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3],
            "image": row[4],
            "category": row[5]
        })

    return render_template(
        "products.html",
        products=products
    )


# =====================================================
# ADD PRODUCT
# =====================================================

@app.route("/add", methods=["GET", "POST"])
def add_product():

    if not admin_required():

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        )

        stock = request.form.get(
            "stock",
            "0"
        )

        category = request.form.get(
            "category",
            "Other"
        ).strip()

        if not name:

            return (
                "Product name is required",
                400
            )

        try:

            price = float(price)
            stock = int(stock)

        except ValueError:

            return (
                "Invalid price or stock",
                400
            )

        if price < 0 or stock < 0:

            return (
                "Price and stock cannot be negative",
                400
            )

        if not category:

            category = "Other"

        image_file = request.files.get(
            "image"
        )

        image_name = None

        if (
            image_file
            and image_file.filename
        ):

            image_name = secure_filename(
                image_file.filename
            )

            image_file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    image_name
                )
            )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (name, price, stock, image, category)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            price,
            stock,
            image_name,
            category
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for("product_list")
        )

    return render_template(
        "add_product.html"
    )


# =====================================================
# ADMIN SELL
# =====================================================

@app.route("/sell/<int:product_id>")
def sell_product(product_id):

    if not admin_required():

        return redirect(
            url_for("login")
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, price, stock
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    if product is None:

        conn.close()

        return redirect(
            url_for("product_list")
        )

    name = product[0]
    price = product[1]
    stock = product[2]

    if stock > 0:

        cursor.execute("""
            UPDATE products
            SET stock = stock - 1
            WHERE id = ?
        """, (product_id,))

        sale_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO sales
            (product_name, price, sale_date)
            VALUES (?, ?, ?)
        """, (
            name,
            price,
            sale_date
        ))

        conn.commit()

    conn.close()

    return redirect(
        url_for("product_list")
    )


# =====================================================
# SALES HISTORY
# =====================================================

@app.route("/sales")
def sales_history():

    if not admin_required():

        return redirect(
            url_for("login")
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, product_name, price, sale_date
        FROM sales
        ORDER BY id DESC
    """)

    sales = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(price), 0)
        FROM sales
    """)

    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
    """)

    total_transactions = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "sales.html",
        sales=sales,
        total_sales=total_sales,
        total_transactions=total_transactions
    )


# =====================================================
# DELETE PRODUCT
# =====================================================

@app.route("/delete/<int:product_id>")
def delete_product(product_id):

    if not admin_required():

        return redirect(
            url_for("login")
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image
        FROM products
        WHERE id = ?
    """, (product_id,))

    result = cursor.fetchone()

    if result and result[0]:

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            result[0]
        )

        if os.path.exists(image_path):

            os.remove(image_path)

    cursor.execute("""
        DELETE FROM products
        WHERE id = ?
        AND stock = 0
    """, (product_id,))

    conn.commit()
    conn.close()

    return redirect(
        url_for("product_list")
    )


# =====================================================
# CUSTOMER SHOP
# =====================================================

@app.route("/customer")
def customer():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, stock, image, category
        FROM products
        ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:

        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3],
            "image": row[4],
            "category": row[5] or "Other"
        })

    cart = session.get(
        "cart",
        {}
    )

    cart_count = sum(
        cart.values()
    )

    return render_template(
        "customer.html",
        products=products,
        cart_count=cart_count
    )


# =====================================================
# ADD TO CART
# =====================================================

@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, stock, image
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    conn.close()

    if product is None:

        return redirect(
            url_for("customer")
        )

    if product[3] <= 0:

        return redirect(
            url_for("customer")
        )

    cart = session.get(
        "cart",
        {}
    )

    key = str(product_id)

    current_quantity = cart.get(
        key,
        0
    )

    if current_quantity < product[3]:

        cart[key] = (
            current_quantity + 1
        )

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =====================================================
# CART
# =====================================================

@app.route("/cart")
def cart():

    cart_data = session.get(
        "cart",
        {}
    )

    items = []

    total = 0

    conn = get_connection()
    cursor = conn.cursor()

    for product_id, quantity in cart_data.items():

        cursor.execute("""
            SELECT id, name, price, stock, image, category
            FROM products
            WHERE id = ?
        """, (int(product_id),))

        product = cursor.fetchone()

        if product is None:
            continue

        available_stock = product[3]

        if quantity > available_stock:

            quantity = available_stock

        if quantity <= 0:
            continue

        subtotal = (
            product[2] * quantity
        )

        total += subtotal

        items.append({
            "id": product[0],
            "name": product[1],
            "price": product[2],
            "stock": product[3],
            "image": product[4],
            "category": product[5],
            "quantity": quantity,
            "subtotal": subtotal
        })

    conn.close()

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


# =====================================================
# REMOVE FROM CART
# =====================================================

@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get(
        "cart",
        {}
    )

    cart.pop(
        str(product_id),
        None
    )

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =====================================================
# INCREASE CART
# =====================================================

@app.route("/cart/increase/<int:product_id>")
def increase_cart(product_id):

    cart = session.get(
        "cart",
        {}
    )

    key = str(product_id)

    current_quantity = cart.get(
        key,
        0
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT stock
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    conn.close()

    if product:

        stock = product[0]

        if current_quantity < stock:

            cart[key] = (
                current_quantity + 1
            )

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =====================================================
# DECREASE CART
# =====================================================

@app.route("/cart/decrease/<int:product_id>")
def decrease_cart(product_id):

    cart = session.get(
        "cart",
        {}
    )

    key = str(product_id)

    current_quantity = cart.get(
        key,
        0
    )

    if current_quantity > 1:

        cart[key] = (
            current_quantity - 1
        )

    else:

        cart.pop(
            key,
            None
        )

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =====================================================
# CHECKOUT
# =====================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    cart_data = session.get(
        "cart",
        {}
    )

    if not cart_data:

        return redirect(
            url_for("customer")
        )

    items = []

    total = 0

    conn = get_connection()
    cursor = conn.cursor()

    for product_id, quantity in cart_data.items():

        cursor.execute("""
            SELECT id, name, price, stock
            FROM products
            WHERE id = ?
        """, (int(product_id),))

        product = cursor.fetchone()

        if product is None:
            continue

        if quantity > product[3]:

            quantity = product[3]

        if quantity <= 0:
            continue

        subtotal = (
            product[2] * quantity
        )

        total += subtotal

        items.append({
            "id": product[0],
            "name": product[1],
            "price": product[2],
            "quantity": quantity,
            "subtotal": subtotal
        })

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        if not customer_name:

            conn.close()

            return render_template(
                "checkout.html",
                items=items,
                total=total,
                error="Please enter your name."
            )

        # Recheck stock
        for item in items:

            cursor.execute("""
                SELECT stock
                FROM products
                WHERE id = ?
            """, (item["id"],))

            stock = cursor.fetchone()[0]

            if stock < item["quantity"]:

                conn.close()

                return render_template(
                    "checkout.html",
                    items=items,
                    total=total,
                    error=(
                        f"Not enough stock for "
                        f"{item['name']}."
                    )
                )

        sale_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Decrease stock
        for item in items:

            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                item["quantity"],
                item["id"]
            ))

            # Add sales records
            for _ in range(
                item["quantity"]
            ):

                cursor.execute("""
                    INSERT INTO sales
                    (product_name, price, sale_date)
                    VALUES (?, ?, ?)
                """, (
                    item["name"],
                    item["price"],
                    sale_date
                ))

        conn.commit()
        conn.close()

        session["cart"] = {}

        return render_template(
            "checkout.html",
            items=items,
            total=total,
            order_success=True,
            customer_name=customer_name,
            phone=phone,
            sale_date=sale_date
        )

    conn.close()

    return render_template(
        "checkout.html",
        items=items,
        total=total
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    create_database()

    print("\n====================================")
    print("      🛒 INSTANTTHINGS")
    print("====================================")
    print("Server running at:")
    print("http://127.0.0.1:5000")
    print("====================================\n")

    app.run(
        debug=True
    )