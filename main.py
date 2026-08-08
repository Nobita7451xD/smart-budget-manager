import csv
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# In a packaged .exe, keep the database beside the executable rather than in
# PyInstaller's temporary extraction folder.
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DB_FILE = APP_DIR / "finance.db"
INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Transport", "Rent", "Bills", "Shopping", "Health", "Education", "Entertainment", "Other"]
COLORS = {"bg": "#08111F", "side": "#0F1B2D", "card": "#14243A", "primary": "#38BDF8", "green": "#22C55E", "red": "#F87171", "yellow": "#FBBF24", "muted": "#94A3B8", "text": "#F8FAFC"}


class SmartBudgetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Smart Budget Manager v1.0")
        self.geometry("1400x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])
        self.user = None
        self.currency = "Rs."
        self._init_database()
        self.show_auth()

    # -------------------- DATABASE --------------------
    def db(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        with self.db() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, currency TEXT DEFAULT 'Rs.', appearance TEXT DEFAULT 'dark');
            CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, amount REAL NOT NULL, source TEXT NOT NULL, date TEXT NOT NULL, description TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, month TEXT NOT NULL, monthly_budget REAL NOT NULL, UNIQUE(username, month));
            """)
            for table in ("income", "expenses"):
                columns = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
                if "description" not in columns:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN description TEXT DEFAULT ''")
            user_columns = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
            if "currency" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'Rs.'")
            if "appearance" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN appearance TEXT DEFAULT 'dark'")
            columns = {r[1] for r in conn.execute("PRAGMA table_info(budget)")}
            if "month" not in columns:
                conn.execute("ALTER TABLE budget ADD COLUMN month TEXT DEFAULT ''")

    # -------------------- COMMON UI --------------------
    def clear(self):
        for child in self.winfo_children(): child.destroy()

    def money(self, value):
        return f"{self.currency} {float(value):,.2f}"

    def month(self): return date.today().strftime("%Y-%m")
    def now(self): return datetime.now().strftime("%A, %d %B %Y  |  %I:%M:%S %p")

    def make_button(self, parent, text, command, **kwargs):
        return ctk.CTkButton(parent, text=text, command=command, fg_color=kwargs.pop("fg_color", COLORS["primary"]), hover_color=kwargs.pop("hover_color", "#0EA5E9"), text_color=kwargs.pop("text_color", "#062033"), font=kwargs.pop("font", ("Segoe UI", 14, "bold")), **kwargs)

    def header(self, title, subtitle=""):
        ctk.CTkLabel(self.content, text=title, font=("Segoe UI", 30, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=36, pady=(25, 0))
        self.clock_label = ctk.CTkLabel(self.content, text=subtitle or f"{self.user}  |  {self.now()}", font=("Segoe UI", 13), text_color=COLORS["muted"])
        self.clock_label.pack(anchor="w", padx=36, pady=(2, 18))
        if not subtitle:
            self.after(1000, self.refresh_clock)

    def refresh_clock(self):
        if self.user and hasattr(self, "clock_label") and self.clock_label.winfo_exists():
            self.clock_label.configure(text=f"{self.user}  |  {self.now()}")
            self.after(1000, self.refresh_clock)

    # -------------------- AUTH --------------------
    def show_auth(self, register=False):
        self.clear()
        wrapper = ctk.CTkFrame(self, fg_color=COLORS["bg"]); wrapper.pack(fill="both", expand=True)
        hero = ctk.CTkFrame(wrapper, width=570, fg_color=COLORS["primary"], corner_radius=0); hero.pack(side="left", fill="both")
        ctk.CTkLabel(hero, text="SMART\nBUDGET", font=("Segoe UI", 44, "bold"), text_color="#062033", justify="center").pack(pady=(210, 12))
        ctk.CTkLabel(hero, text="Take control of every rupee.", font=("Segoe UI", 18), text_color="#062033").pack()
        panel = ctk.CTkFrame(wrapper, fg_color=COLORS["bg"], corner_radius=0); panel.pack(side="right", fill="both", expand=True)
        title = "Create your account" if register else "Welcome back"
        ctk.CTkLabel(panel, text=title, font=("Segoe UI", 30, "bold"), text_color=COLORS["text"]).pack(pady=(150, 8))
        ctk.CTkLabel(panel, text="Your personal finance dashboard", text_color=COLORS["muted"]).pack()
        username = ctk.CTkEntry(panel, width=340, height=46, placeholder_text="Username"); username.pack(pady=(38, 10))
        password = ctk.CTkEntry(panel, width=340, height=46, placeholder_text="Password", show="*"); password.pack(pady=10)
        confirm = None
        if register:
            confirm = ctk.CTkEntry(panel, width=340, height=46, placeholder_text="Confirm password", show="*"); confirm.pack(pady=10)
        action = lambda: self.register(username.get(), password.get(), confirm.get()) if register else self.login(username.get(), password.get())
        self.make_button(panel, "Create account" if register else "Login", action, width=340, height=46).pack(pady=22)
        self.make_button(panel, "Back to login" if register else "Create a new account", lambda: self.show_auth(not register), width=340, height=42, fg_color="transparent", hover_color=COLORS["card"], text_color=COLORS["primary"], border_width=1).pack()
        username.bind("<Return>", lambda e: password.focus_set())
        password.bind("<Return>", lambda e: action())
        if confirm: confirm.bind("<Return>", lambda e: action())
        username.focus_set()

    def login(self, username, password):
        with self.db() as conn: row = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username.strip(), password)).fetchone()
        if not row: messagebox.showerror("Login failed", "Incorrect username or password."); return
        self.user, self.currency = row["username"], row["currency"] or "Rs."
        ctk.set_appearance_mode(row["appearance"] or "dark")
        self.build_shell(); self.show_dashboard()

    def register(self, username, password, confirm):
        username = username.strip()
        if len(username) < 3 or len(password) < 4: messagebox.showerror("Invalid details", "Username must have 3+ and password 4+ characters."); return
        if password != confirm: messagebox.showerror("Password mismatch", "Both passwords must match."); return
        try:
            with self.db() as conn: conn.execute("INSERT INTO users(username,password) VALUES(?,?)", (username, password))
        except sqlite3.IntegrityError: messagebox.showerror("Account exists", "Choose a different username."); return
        messagebox.showinfo("Account created", "Account created successfully. Please login."); self.show_auth()

    # -------------------- SHELL + DASHBOARD --------------------
    def build_shell(self):
        self.clear(); shell = ctk.CTkFrame(self, fg_color=COLORS["bg"]); shell.pack(fill="both", expand=True)
        side = ctk.CTkFrame(shell, width=235, fg_color=COLORS["side"], corner_radius=0); side.pack(side="left", fill="y"); side.pack_propagate(False)
        ctk.CTkLabel(side, text="SMART", font=("Segoe UI", 25, "bold"), text_color=COLORS["primary"]).pack(pady=(35, 0))
        ctk.CTkLabel(side, text="BUDGET", font=("Segoe UI", 25, "bold"), text_color=COLORS["text"]).pack()
        ctk.CTkLabel(side, text="PERSONAL FINANCE", font=("Segoe UI", 10, "bold"), text_color=COLORS["muted"]).pack(pady=(2, 30))
        for label, view in [("Dashboard", self.show_dashboard), ("Income", self.show_income), ("Expenses", self.show_expenses), ("Budget", self.show_budget), ("Reports", self.show_reports), ("Export", self.show_export), ("Settings", self.show_settings)]:
            self.make_button(side, label, view, width=190, height=40, fg_color="transparent", hover_color=COLORS["card"], text_color=COLORS["text"], anchor="w").pack(pady=4)
        self.make_button(side, "Logout", self.logout, width=190, height=40, fg_color="transparent", hover_color="#4B1F2A", text_color=COLORS["red"], anchor="w").pack(side="bottom", pady=28)
        ctk.CTkLabel(side, text="Developed by Shubham", font=("Segoe UI", 11), text_color=COLORS["muted"]).pack(side="bottom", pady=4)
        self.content = ctk.CTkFrame(shell, fg_color=COLORS["bg"], corner_radius=0); self.content.pack(side="right", fill="both", expand=True)

    def wipe_content(self):
        for child in self.content.winfo_children(): child.destroy()

    def totals(self, month=None):
        prefix = (month or self.month()) + "%"
        with self.db() as conn:
            income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE username=? AND date LIKE ?", (self.user, prefix)).fetchone()[0]
            expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE username=? AND date LIKE ?", (self.user, prefix)).fetchone()[0]
            budget = conn.execute("SELECT monthly_budget FROM budget WHERE username=? AND month=?", (self.user, month or self.month())).fetchone()
        return float(income), float(expense), float(budget[0]) if budget else 0.0

    def card(self, parent, title, value, color, note=""):
        box = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=14, height=120); box.pack(side="left", fill="x", expand=True, padx=7); box.pack_propagate(False)
        ctk.CTkLabel(box, text=title, font=("Segoe UI", 13), text_color=COLORS["muted"]).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(box, text=self.money(value), font=("Segoe UI", 23, "bold"), text_color=color).pack(anchor="w", padx=18, pady=(2, 0))
        if note: ctk.CTkLabel(box, text=note, font=("Segoe UI", 11), text_color=COLORS["muted"]).pack(anchor="w", padx=18)

    def show_dashboard(self):
        self.wipe_content(); self.header("Dashboard")
        income, expense, budget = self.totals(); balance = income-expense
        hero = ctk.CTkFrame(self.content, fg_color=COLORS["primary"], corner_radius=16); hero.pack(fill="x", padx=35, pady=(0, 15))
        advice = "Add a monthly budget to unlock spending alerts." if not budget else ("Great job! Your spending is within budget." if expense <= budget else "Warning: you have exceeded this month's budget.")
        ctk.CTkLabel(hero, text="Financial command center", font=("Segoe UI", 22, "bold"), text_color="#062033").pack(anchor="w", padx=22, pady=(16, 0))
        ctk.CTkLabel(hero, text=advice, font=("Segoe UI", 13), text_color="#062033").pack(anchor="w", padx=22, pady=(2, 16))
        row = ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", padx=28)
        self.card(row, "Monthly income", income, COLORS["green"], "Money earned")
        self.card(row, "Monthly expenses", expense, COLORS["red"], "Money spent")
        self.card(row, "Available balance", balance, COLORS["primary"], "Income minus expenses")
        self.card(row, "Budget remaining", budget-expense, COLORS["yellow"], "Monthly target")
        actions = ctk.CTkFrame(self.content, fg_color="transparent"); actions.pack(fill="x", padx=35, pady=(18, 3))
        ctk.CTkLabel(actions, text="Quick actions", font=("Segoe UI", 19, "bold"), text_color=COLORS["text"]).pack(side="left")
        self.make_button(actions, "+ Add income", self.show_income, width=145, height=36).pack(side="right", padx=5)
        self.make_button(actions, "+ Add expense", self.show_expenses, width=145, height=36, fg_color=COLORS["yellow"], hover_color="#D97706").pack(side="right", padx=5)
        ctk.CTkLabel(self.content, text="Recent transactions", font=("Segoe UI", 19, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=35, pady=(12, 5))
        self.transaction_table(limit=8)

    # -------------------- TRANSACTIONS --------------------
    def transaction_table(self, kind=None, limit=50):
        frame = ctk.CTkScrollableFrame(self.content, fg_color=COLORS["card"], corner_radius=12); frame.pack(fill="both", expand=True, padx=35, pady=(0, 24))
        query = "SELECT id, source AS category, amount, date, description, 'Income' AS type FROM income WHERE username=? UNION ALL SELECT id, category, amount, date, description, 'Expense' AS type FROM expenses WHERE username=? ORDER BY date DESC, id DESC LIMIT ?"
        with self.db() as conn: rows = conn.execute(query, (self.user, self.user, limit)).fetchall()
        if kind: rows = [r for r in rows if r["type"] == kind]
        if not rows: ctk.CTkLabel(frame, text="No transactions yet. Start by adding one above.", text_color=COLORS["muted"]).pack(pady=28); return
        for r in rows:
            line = ctk.CTkFrame(frame, fg_color="transparent"); line.pack(fill="x", padx=13, pady=5)
            color = COLORS["green"] if r["type"] == "Income" else COLORS["red"]
            sign = "+" if r["type"] == "Income" else "-"
            ctk.CTkLabel(line, text=f"{r['date']}  |  {r['type']}  |  {r['category']}\n{r['description'] or 'No description'}", justify="left", font=("Segoe UI", 13), text_color=COLORS["text"]).pack(side="left")
            self.make_button(line, "Edit", lambda x=r: self.edit_transaction(x), width=54, height=30, fg_color=COLORS["card"], hover_color="#23415F", text_color=COLORS["primary"]).pack(side="right", padx=4)
            self.make_button(line, "Delete", lambda x=r: self.delete_transaction(x), width=65, height=30, fg_color=COLORS["card"], hover_color="#4B1F2A", text_color=COLORS["red"]).pack(side="right", padx=4)
            ctk.CTkLabel(line, text=f"{sign} {self.money(r['amount'])}", font=("Segoe UI", 14, "bold"), text_color=color).pack(side="right", padx=12)

    def transaction_form(self, transaction_type, record=None):
        self.wipe_content(); self.header(f"{'Edit' if record else 'Add'} {transaction_type}")
        categories = INCOME_CATEGORIES if transaction_type == "Income" else EXPENSE_CATEGORIES
        card = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=14); card.pack(fill="x", padx=35, pady=6)
        amount = ctk.CTkEntry(card, placeholder_text="Amount", width=360, height=42); amount.pack(anchor="w", padx=28, pady=(25, 8))
        category = ctk.CTkComboBox(card, values=categories, width=360, height=42); category.pack(anchor="w", padx=28, pady=8)
        entered_date = ctk.CTkEntry(card, placeholder_text="YYYY-MM-DD", width=360, height=42); entered_date.pack(anchor="w", padx=28, pady=8)
        description = ctk.CTkEntry(card, placeholder_text="Description (optional)", width=360, height=42); description.pack(anchor="w", padx=28, pady=8)
        if record:
            amount.insert(0, str(record["amount"])); category.set(record["category"]); entered_date.insert(0, record["date"]); description.insert(0, record["description"] or "")
        else: category.set(categories[0]); entered_date.insert(0, date.today().isoformat())
        save = lambda: self.save_transaction(transaction_type, amount.get(), category.get(), entered_date.get(), description.get(), record["id"] if record else None)
        self.make_button(card, "Update transaction" if record else "Save transaction", save, width=360, height=42).pack(anchor="w", padx=28, pady=(10, 25))
        amount.focus_set(); entered_date.bind("<Return>", lambda e: save())

    def save_transaction(self, kind, amount, category, entered_date, description, record_id=None):
        try:
            value = float(amount); datetime.strptime(entered_date, "%Y-%m-%d")
            if value <= 0: raise ValueError
        except ValueError: messagebox.showerror("Invalid details", "Use a positive amount and date format YYYY-MM-DD."); return
        table, label = ("income", "source") if kind == "Income" else ("expenses", "category")
        with self.db() as conn:
            if record_id: conn.execute(f"UPDATE {table} SET amount=?, {label}=?, date=?, description=? WHERE id=? AND username=?", (value, category, entered_date, description.strip(), record_id, self.user))
            else: conn.execute(f"INSERT INTO {table}(username,amount,{label},date,description) VALUES(?,?,?,?,?)", (self.user, value, category, entered_date, description.strip()))
        messagebox.showinfo("Saved", f"{kind} saved successfully."); self.show_income() if kind == "Income" else self.show_expenses()

    def edit_transaction(self, record): self.transaction_form(record["type"], record)
    def delete_transaction(self, record):
        if not messagebox.askyesno("Delete transaction", "Do you want to permanently delete this transaction?"): return
        table = "income" if record["type"] == "Income" else "expenses"
        with self.db() as conn: conn.execute(f"DELETE FROM {table} WHERE id=? AND username=?", (record["id"], self.user))
        self.show_income() if record["type"] == "Income" else self.show_expenses()

    def show_income(self):
        self.transaction_form("Income")
        ctk.CTkLabel(self.content, text="Income history", font=("Segoe UI", 19, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=35, pady=(18, 6))
        self.transaction_table("Income")
    def show_expenses(self):
        self.transaction_form("Expense")
        ctk.CTkLabel(self.content, text="Expense history", font=("Segoe UI", 19, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=35, pady=(18, 6))
        self.transaction_table("Expense")

    # -------------------- BUDGET + REPORTS --------------------
    def show_budget(self, selected_month=None):
        self.wipe_content(); self.header("Monthly Budget")
        budget_month = selected_month or self.month()
        income, spent, budget = self.totals(budget_month); remaining = budget-spent; ratio = spent/budget if budget else 0
        with self.db() as conn:
            months = [r[0] for r in conn.execute("SELECT DISTINCT month FROM budget WHERE username=? AND month <> '' ORDER BY month DESC", (self.user,)).fetchall()]
        if budget_month not in months: months.insert(0, budget_month)
        selector = ctk.CTkFrame(self.content, fg_color="transparent"); selector.pack(fill="x", padx=35, pady=(0, 5))
        ctk.CTkLabel(selector, text="Budget month", text_color=COLORS["muted"]).pack(side="left", padx=(0, 8))
        month_box = ctk.CTkComboBox(selector, values=months, width=150); month_box.set(budget_month); month_box.pack(side="left")
        self.make_button(selector, "View month", lambda: self.show_budget(month_box.get()), width=115, height=32).pack(side="left", padx=8)
        panel = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=14); panel.pack(fill="x", padx=35, pady=4)
        status = "No budget set" if not budget else ("Overspending alert" if remaining < 0 else "On track")
        ctk.CTkLabel(panel, text=status, font=("Segoe UI", 20, "bold"), text_color=COLORS["red"] if remaining < 0 else COLORS["green"]).pack(anchor="w", padx=25, pady=(22, 4))
        ctk.CTkLabel(panel, text=f"Spent {self.money(spent)} of {self.money(budget)}  |  Remaining: {self.money(remaining)}", font=("Segoe UI", 15), text_color=COLORS["text"]).pack(anchor="w", padx=25)
        bar = ctk.CTkProgressBar(panel, width=700, progress_color=COLORS["red"] if ratio > 1 else COLORS["primary"]); bar.pack(anchor="w", padx=25, pady=(18, 8)); bar.set(min(ratio, 1))
        ctk.CTkLabel(panel, text=f"{ratio*100:.1f}% used", text_color=COLORS["muted"]).pack(anchor="w", padx=25, pady=(0, 20))
        entry = ctk.CTkEntry(self.content, placeholder_text="Set budget for current month", width=360, height=42); entry.pack(anchor="w", padx=35, pady=(24, 8))
        self.make_button(self.content, "Save monthly budget", lambda: self.save_budget(entry.get(), budget_month), width=360, height=42).pack(anchor="w", padx=35)

    def save_budget(self, raw, budget_month=None):
        try: value = float(raw); assert value >= 0
        except (ValueError, AssertionError): messagebox.showerror("Invalid budget", "Enter a valid positive budget."); return
        # Compatible with both fresh and older databases that do not have a UNIQUE index.
        with self.db() as conn:
            conn.execute("DELETE FROM budget WHERE username=? AND month=?", (self.user, budget_month or self.month()))
            conn.execute("INSERT INTO budget(username,month,monthly_budget) VALUES(?,?,?)", (self.user, budget_month or self.month(), value))
        self.show_budget(budget_month)

    def show_reports(self, selected_month=None):
        self.wipe_content(); self.header("Reports & Analytics")
        report_month = selected_month or self.month()
        income, expense, budget = self.totals(report_month); savings = income-expense
        with self.db() as conn:
            available_months = [r[0] for r in conn.execute("SELECT DISTINCT substr(date,1,7) FROM (SELECT date FROM income WHERE username=? UNION SELECT date FROM expenses WHERE username=?) WHERE substr(date,1,7) <> '' ORDER BY 1 DESC", (self.user, self.user)).fetchall()]
        if report_month not in available_months: available_months.insert(0, report_month)
        filter_row = ctk.CTkFrame(self.content, fg_color="transparent"); filter_row.pack(fill="x", padx=35, pady=(0, 8))
        ctk.CTkLabel(filter_row, text="Report month", text_color=COLORS["muted"]).pack(side="left", padx=(0, 8))
        month_box = ctk.CTkComboBox(filter_row, values=available_months, width=150); month_box.set(report_month); month_box.pack(side="left")
        self.make_button(filter_row, "Apply filter", lambda: self.show_reports(month_box.get()), width=120, height=32).pack(side="left", padx=8)
        summary = ctk.CTkFrame(self.content, fg_color="transparent"); summary.pack(fill="x", padx=28)
        self.card(summary, "Income", income, COLORS["green"]); self.card(summary, "Expenses", expense, COLORS["red"]); self.card(summary, "Savings", savings, COLORS["primary"]); self.card(summary, "Budget usage", (expense/budget*100 if budget else 0), COLORS["yellow"], "Percent")
        with self.db() as conn:
            cats = conn.execute("SELECT category, SUM(amount) total FROM expenses WHERE username=? AND date LIKE ? GROUP BY category ORDER BY total DESC", (self.user, report_month+"%")).fetchall()
            months = conn.execute("SELECT substr(date,1,7) month, SUM(amount) total FROM expenses WHERE username=? GROUP BY substr(date,1,7) ORDER BY month DESC LIMIT 6", (self.user,)).fetchall()[::-1]
        if cats: ctk.CTkLabel(self.content, text=f"Top spending category: {cats[0]['category']} ({self.money(cats[0]['total'])})", text_color=COLORS["yellow"], font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=35, pady=(18, 2))
        charts = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=14); charts.pack(fill="both", expand=True, padx=35, pady=(10, 25))
        figure = Figure(figsize=(11, 3.4), facecolor=COLORS["card"]); figure.subplots_adjust(wspace=.42)
        ax1 = figure.add_subplot(131); ax2 = figure.add_subplot(132); ax3 = figure.add_subplot(133)
        ax1.set_facecolor(COLORS["card"]); ax2.set_facecolor(COLORS["card"]); ax3.set_facecolor(COLORS["card"])
        if cats: ax1.pie([r["total"] for r in cats], labels=[r["category"] for r in cats], autopct="%1.0f%%", textprops={"color": "white", "fontsize": 8})
        else: ax1.text(.5, .5, "No expense data", ha="center", va="center", color="white"); ax1.set_xticks([]); ax1.set_yticks([])
        ax1.set_title("Expense by category", color="white")
        labels = [r["month"] for r in months]; values = [r["total"] for r in months]
        ax2.bar(labels, values, color=COLORS["primary"]); ax2.set_title("Monthly spending", color="white"); ax2.tick_params(axis="x", labelrotation=35, colors="white"); ax2.tick_params(axis="y", colors="white"); [s.set_color(COLORS["muted"]) for s in ax2.spines.values()]
        ax3.bar(["Income", "Expense", "Savings"], [income, expense, savings], color=[COLORS["green"], COLORS["red"], COLORS["primary"]])
        ax3.set_title("Income vs expense", color="white"); ax3.tick_params(axis="x", labelrotation=20, colors="white"); ax3.tick_params(axis="y", colors="white"); [s.set_color(COLORS["muted"]) for s in ax3.spines.values()]
        canvas = FigureCanvasTkAgg(figure, charts); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    # -------------------- EXPORT + SETTINGS --------------------
    def all_transactions(self):
        with self.db() as conn: return conn.execute("SELECT date, 'Income' type, source category, description, amount FROM income WHERE username=? UNION ALL SELECT date, 'Expense', category, description, amount FROM expenses WHERE username=? ORDER BY date", (self.user, self.user)).fetchall()

    def show_export(self):
        self.wipe_content(); self.header("Export financial data", "Save your transactions and summary for sharing or submission.")
        box = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=14); box.pack(fill="x", padx=35, pady=8)
        for text, command, desc in [("Export CSV", self.export_csv, "Universal spreadsheet format"), ("Export Excel", self.export_excel, "Formatted .xlsx workbook"), ("Generate PDF report", self.export_pdf, "Monthly financial summary")]:
            row = ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=22, pady=12)
            self.make_button(row, text, command, width=190, height=40).pack(side="left")
            ctk.CTkLabel(row, text=desc, text_color=COLORS["muted"]).pack(side="left", padx=16)

    def export_path(self, extension): return filedialog.asksaveasfilename(defaultextension=extension, filetypes=[(extension.upper().replace('.', '') + " file", "*" + extension)])
    def export_csv(self):
        path = self.export_path(".csv")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f); writer.writerow(["Date", "Type", "Category", "Description", "Amount"]); writer.writerows([tuple(r) for r in self.all_transactions()])
        messagebox.showinfo("Export complete", "CSV file saved successfully.")
    def export_excel(self):
        path = self.export_path(".xlsx")
        if not path: return
        book = Workbook(); sheet = book.active; sheet.title = "Transactions"; sheet.append(["Date", "Type", "Category", "Description", "Amount"])
        for row in self.all_transactions(): sheet.append(tuple(row))
        for col in sheet.columns: sheet.column_dimensions[col[0].column_letter].width = 18
        book.save(path); messagebox.showinfo("Export complete", "Excel workbook saved successfully.")
    def export_pdf(self):
        path = self.export_path(".pdf")
        if not path: return
        income, expense, budget = self.totals(); styles = getSampleStyleSheet(); items = [Paragraph("Smart Budget Manager - Monthly Report", styles["Title"]), Spacer(1, 14), Paragraph(f"User: {self.user} | Month: {date.today().strftime('%B %Y')}", styles["Normal"]), Spacer(1, 12)]
        table = Table([["Metric", "Amount"], ["Income", self.money(income)], ["Expenses", self.money(expense)], ["Savings", self.money(income-expense)], ["Budget", self.money(budget)]])
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#38BDF8")), ("GRID", (0,0), (-1,-1), .5, colors.grey), ("PADDING", (0,0), (-1,-1), 8)])); items += [table, Spacer(1, 14), Paragraph("Recent transactions", styles["Heading2"])]
        rows = [["Date", "Type", "Category", "Amount"]] + [[r["date"], r["type"], r["category"], self.money(r["amount"])] for r in self.all_transactions()[-20:]]
        tx = Table(rows); tx.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DCEEF7")), ("GRID", (0,0), (-1,-1), .25, colors.grey), ("PADDING", (0,0), (-1,-1), 5)])); items.append(tx)
        SimpleDocTemplate(path, pagesize=A4).build(items); messagebox.showinfo("Report ready", "PDF financial report saved successfully.")

    def show_settings(self):
        self.wipe_content(); self.header("Settings")
        card = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=14); card.pack(fill="x", padx=35, pady=8)
        ctk.CTkLabel(card, text=f"Profile: {self.user}", font=("Segoe UI", 18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=24, pady=(22, 12))
        new_name = ctk.CTkEntry(card, placeholder_text="New username", width=340); new_name.pack(anchor="w", padx=24, pady=5)
        self.make_button(card, "Change username", lambda: self.change_username(new_name.get()), width=340, height=36).pack(anchor="w", padx=24, pady=(3, 16))
        current = ctk.CTkEntry(card, placeholder_text="Current password", show="*", width=340); current.pack(anchor="w", padx=24, pady=5)
        new_pass = ctk.CTkEntry(card, placeholder_text="New password", show="*", width=340); new_pass.pack(anchor="w", padx=24, pady=5)
        self.make_button(card, "Change password", lambda: self.change_password(current.get(), new_pass.get()), width=340, height=36).pack(anchor="w", padx=24, pady=(3, 16))
        currency = ctk.CTkComboBox(card, values=["Rs.", "$", "EUR", "GBP"], width=340); currency.set(self.currency); currency.pack(anchor="w", padx=24, pady=5)
        self.make_button(card, "Save currency", lambda: self.save_currency(currency.get()), width=340, height=36).pack(anchor="w", padx=24, pady=(3, 16))
        mode = ctk.CTkComboBox(card, values=["dark", "light", "system"], width=340); mode.set("dark"); mode.pack(anchor="w", padx=24, pady=5)
        self.make_button(card, "Apply appearance", lambda: self.save_appearance(mode.get()), width=340, height=36).pack(anchor="w", padx=24, pady=(3, 24))

    def change_username(self, name):
        name = name.strip()
        if len(name) < 3: messagebox.showerror("Invalid name", "Username must have 3+ characters."); return
        try:
            with self.db() as conn:
                for table in ("users", "income", "expenses", "budget"): conn.execute(f"UPDATE {table} SET username=? WHERE username=?", (name, self.user))
        except sqlite3.IntegrityError: messagebox.showerror("Unavailable", "That username is already taken."); return
        self.user = name; self.show_settings()
    def change_password(self, current, new):
        if len(new) < 4: messagebox.showerror("Invalid password", "New password must have 4+ characters."); return
        with self.db() as conn: result = conn.execute("UPDATE users SET password=? WHERE username=? AND password=?", (new, self.user, current))
        messagebox.showinfo("Updated", "Password changed successfully.") if result.rowcount else messagebox.showerror("Incorrect password", "Your current password is incorrect.")
    def save_currency(self, value):
        self.currency = value
        with self.db() as conn: conn.execute("UPDATE users SET currency=? WHERE username=?", (value, self.user))
        self.show_settings()
    def save_appearance(self, value):
        ctk.set_appearance_mode(value)
        with self.db() as conn: conn.execute("UPDATE users SET appearance=? WHERE username=?", (value, self.user))
    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to logout?"):
            self.user = None; self.show_auth()


if __name__ == "__main__":
    SmartBudgetApp().mainloop()
