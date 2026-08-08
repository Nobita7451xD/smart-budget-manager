"""Shareable web edition of Smart Budget Manager."""
import csv
import sqlite3
from datetime import date
from io import StringIO
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for, Response

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "finance.db"
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-before-public-deployment"
INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Transport", "Rent", "Bills", "Shopping", "Health", "Education", "Entertainment", "Other"]


def db():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, currency TEXT DEFAULT 'Rs.');
        CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, amount REAL NOT NULL, source TEXT NOT NULL, date TEXT NOT NULL, description TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, month TEXT NOT NULL, monthly_budget REAL NOT NULL);
        """)
        for table in ("users", "income", "expenses", "budget"):
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if table == "users" and "currency" not in cols: conn.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'Rs.'")
            if table in ("income", "expenses") and "description" not in cols: conn.execute(f"ALTER TABLE {table} ADD COLUMN description TEXT DEFAULT ''")
            if table == "budget" and "month" not in cols: conn.execute("ALTER TABLE budget ADD COLUMN month TEXT DEFAULT ''")


def username(): return session.get("username")
def current_month(): return date.today().strftime("%Y-%m")


@app.before_request
def setup():
    initialize_database()


@app.route("/", methods=["GET"])
def home():
    if not username(): return redirect(url_for("login"))
    month = request.args.get("month", current_month())
    with db() as conn:
        income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE username=? AND date LIKE ?", (username(), month + "%")).fetchone()[0]
        expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE username=? AND date LIKE ?", (username(), month + "%")).fetchone()[0]
        budget_row = conn.execute("SELECT monthly_budget FROM budget WHERE username=? AND month=? ORDER BY id DESC LIMIT 1", (username(), month)).fetchone()
        transactions = conn.execute("SELECT id, date, source category, description, amount, 'Income' type FROM income WHERE username=? UNION ALL SELECT id, date, category, description, amount, 'Expense' FROM expenses WHERE username=? ORDER BY date DESC, id DESC LIMIT 15", (username(), username())).fetchall()
        categories = conn.execute("SELECT category, SUM(amount) total FROM expenses WHERE username=? AND date LIKE ? GROUP BY category ORDER BY total DESC", (username(), month + "%")).fetchall()
        months = conn.execute("SELECT DISTINCT substr(date,1,7) m FROM (SELECT date FROM income WHERE username=? UNION SELECT date FROM expenses WHERE username=?) ORDER BY m DESC", (username(), username())).fetchall()
    budget = float(budget_row[0]) if budget_row else 0
    return render_template("dashboard.html", income=float(income), expense=float(expense), budget=budget, balance=float(income-expense), transactions=transactions, categories=categories, month=month, months=[r[0] for r in months if r[0]], today=date.today().isoformat(), income_categories=INCOME_CATEGORIES, expense_categories=EXPENSE_CATEGORIES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with db() as conn: user = conn.execute("SELECT username FROM users WHERE username=? AND password=?", (request.form["username"].strip(), request.form["password"])).fetchone()
        if user: session["username"] = user["username"]; return redirect(url_for("home"))
        flash("Wrong username or password.", "error")
    return render_template("auth.html", mode="login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, password, confirm = request.form["username"].strip(), request.form["password"], request.form["confirm"]
        if len(name) < 3 or len(password) < 4: flash("Username must be 3+ and password 4+ characters.", "error")
        elif password != confirm: flash("Passwords do not match.", "error")
        else:
            try:
                with db() as conn: conn.execute("INSERT INTO users(username,password) VALUES(?,?)", (name, password))
                flash("Account created. Login to continue.", "success"); return redirect(url_for("login"))
            except sqlite3.IntegrityError: flash("Username already exists.", "error")
    return render_template("auth.html", mode="register")


@app.post("/transaction")
def add_transaction():
    if not username(): return redirect(url_for("login"))
    kind, category, raw_amount, entered_date = request.form["type"], request.form["category"], request.form["amount"], request.form["date"]
    try: amount = float(raw_amount); assert amount > 0; date.fromisoformat(entered_date)
    except (ValueError, AssertionError): flash("Enter a positive amount and a valid date.", "error"); return redirect(url_for("home"))
    table, field = ("income", "source") if kind == "Income" else ("expenses", "category")
    with db() as conn: conn.execute(f"INSERT INTO {table}(username,amount,{field},date,description) VALUES(?,?,?,?,?)", (username(), amount, category, entered_date, request.form.get("description", "").strip()))
    flash(f"{kind} saved successfully.", "success"); return redirect(url_for("home"))


@app.post("/budget")
def save_budget():
    if not username(): return redirect(url_for("login"))
    month = request.form.get("month", current_month())
    try: amount = float(request.form["amount"]); assert amount >= 0
    except (ValueError, AssertionError): flash("Enter a valid budget.", "error"); return redirect(url_for("home"))
    with db() as conn:
        conn.execute("DELETE FROM budget WHERE username=? AND month=?", (username(), month))
        conn.execute("INSERT INTO budget(username,month,monthly_budget) VALUES(?,?,?)", (username(), month, amount))
    flash("Monthly budget saved.", "success"); return redirect(url_for("home", month=month))


@app.post("/delete/<kind>/<int:transaction_id>")
def delete_transaction(kind, transaction_id):
    if not username(): return redirect(url_for("login"))
    table = "income" if kind == "Income" else "expenses"
    with db() as conn: conn.execute(f"DELETE FROM {table} WHERE id=? AND username=?", (transaction_id, username()))
    flash("Transaction deleted.", "success"); return redirect(url_for("home"))


@app.get("/export/csv")
def export_csv():
    if not username(): return redirect(url_for("login"))
    with db() as conn: rows = conn.execute("SELECT date, 'Income' type, source category, description, amount FROM income WHERE username=? UNION ALL SELECT date, 'Expense', category, description, amount FROM expenses WHERE username=? ORDER BY date", (username(), username())).fetchall()
    output = StringIO(); writer = csv.writer(output); writer.writerow(["Date", "Type", "Category", "Description", "Amount"]); writer.writerows([tuple(row) for row in rows])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=smart-budget-transactions.csv"})


@app.get("/logout")
def logout(): session.clear(); return redirect(url_for("login"))


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
