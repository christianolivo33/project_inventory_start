from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect
import sqlite3
import os
import random
import string

# -----------------------------
# FLASK APP SETUP
# -----------------------------
app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DB = "inventory.db"

# -----------------------------
# SKU GENERATOR (INCREMENTING)
# -----------------------------
def generate_sku():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT sku FROM items ORDER BY id DESC LIMIT 1")
    last = c.fetchone()
    conn.close()

    if last and last["sku"] and last["sku"].startswith("SKU"):
        try:
            num = int(last["sku"].replace("SKU", ""))
            new_num = num + 1
        except:
            new_num = 1
    else:
        new_num = 1

    return f"SKU{new_num:07d}"


# -----------------------------
# DATABASE SETUP
# -----------------------------
def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                quantity INTEGER,
                price REAL,
                category TEXT,
                supplier TEXT,
                reorder_level INTEGER,
                image_url TEXT,
                sku TEXT
            )
        """)
        conn.commit()
        conn.close()

init_db()

# -----------------------------
# DB QUERY HELPER
# -----------------------------
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def index():
    search = request.args.get("search", "")
    sort = request.args.get("sort", "name")

    items = query_db(f"""
        SELECT * FROM items
        WHERE name LIKE ?
        ORDER BY {sort} ASC
    """, (f"%{search}%",))

    total_value = sum(i["quantity"] * i["price"] for i in items)

    return render_template("index.html", items=items, total_value=total_value)

@app.route("/edit/<int:item_id>")
def edit(item_id):
    item = query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True)
    return render_template("edit.html", item=item)

@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    data = (
        request.form["name"],
        request.form["quantity"],
        request.form["price"],
        request.form["category"],
        request.form["supplier"],
        request.form["reorder_level"],
        request.form["image_url"],
        item_id
    )

    query_db("""
        UPDATE items
        SET name=?, quantity=?, price=?, category=?, supplier=?, reorder_level=?, image_url=?
        WHERE id=?
    """, data)

    return redirect("/")

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    query_db("DELETE FROM items WHERE id=?", (item_id,))
    return redirect("/")

@app.route("/add", methods=["POST"])
def add():
    image = request.files.get("image")
    filename = None

    if image and image.filename != "":
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    # SKU comes from the form (pre‑generated on /add-item)
    sku = request.form["sku"]

    data = (
        request.form["name"],
        request.form["quantity"],
        request.form["price"],
        request.form["category"],
        request.form["supplier"],
        request.form["reorder_level"],
        filename,
        sku
    )

    query_db("""
        INSERT INTO items (name, quantity, price, category, supplier, reorder_level, image_url, sku)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    return redirect("/")

@app.route("/dashboard")
def dashboard():
    items = query_db("SELECT * FROM items")

    total_value = sum(i["quantity"] * i["price"] for i in items)
    low_stock = [i for i in items if i["quantity"] <= i["reorder_level"]]

    category_counts = {}
    for i in items:
        category_counts[i["category"]] = category_counts.get(i["category"], 0) + 1

    return render_template("dashboard.html",
                           total_value=total_value,
                           low_stock=low_stock,
                           category_counts=category_counts)

CATEGORIES = ["Electronics", "Food", "Clothing", "Tools", "Office", "Other"]

@app.route("/add-item")
def add_item_page():
    sku = generate_sku()
    return render_template("add_item.html", categories=CATEGORIES, generated_sku=sku)

@app.route("/item/<int:item_id>")
def item_detail(item_id):
    item = query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True)
    return render_template("item_detail.html", item=item)


if __name__ == "__main__":
    app.run(debug=True)
