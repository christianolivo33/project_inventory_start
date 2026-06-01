from flask import Flask, render_template, request, redirect
import csv
import os

app = Flask(__name__)

CSV_FILE = "inventory.csv"

# Ensure CSV exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "quantity", "price"])

def read_inventory():
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)

def add_item(name, quantity, price):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, quantity, price])

@app.route("/")
def index():
    items = read_inventory()
    return render_template("index.html", items=items)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    add_item(name, quantity, price)
    return redirect("/")

#Route to show the edit page
@app.route("/edit/<int:index>")
def edit(index):
    items = read_inventory()
    item = items[index]
    return render_template("edit.html", item=item, index=index)

@app.route("/update/<int:index>", methods=["POST"])
def update(index):
    items = read_inventory()

    # Update values
    items[index]["name"] = request.form["name"]
    items[index]["quantity"] = request.form["quantity"]
    items[index]["price"] = request.form["price"]

    # Rewrite CSV
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "quantity", "price"])
        for item in items:
            writer.writerow([item["name"], item["quantity"], item["price"]])

    return redirect("/")


@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    items = read_inventory()



    # Remove the item at the given index
    items.pop(index)

    # Rewrite the CSV file
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "quantity", "price"])
        for item in items:
            writer.writerow([item["name"], item["quantity"], item["price"]])

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)


