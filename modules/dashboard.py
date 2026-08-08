import sqlite3
from datetime import date, datetime
import customtkinter as ctk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.charts import expense_pie_chart
from utils.theme import *


class Dashboard:
    def __init__(self, username):
        self.username = username
        self.root = ctk.CTk()
        self.root.title("Smart Budget Manager")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.configure(fg_color=BG_COLOR)
        self._build_layout()
        self.show_dashboard()
        self.root.mainloop()

    def _connection(self):
        connection = sqlite3.connect("finance.db")
        connection.row_factory = sqlite3.Row
        return connection

    def _build_layout(self):
        sidebar = ctk.CTkFrame(self.root, width=230, fg_color=SIDEBAR, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(sidebar, text="SMART", font=("Segoe UI", 24, "bold"), text_color=PRIMARY).pack(pady=(38, 0))
        ctk.CTkLabel(sidebar, text="BUDGET", font=("Segoe UI", 24, "bold")).pack(pady=(0, 30))
        ctk.CTkLabel(sidebar, text="PERSONAL FINANCE", font=SMALL_FONT, text_color=TEXT_SECONDARY).pack(pady=(0, 22))
        for label, callback in [
            ("Dashboard", self.show_dashboard), ("Income", self.show_income),
            ("Expense", self.show_expense), ("Budget", self.show_budget),
            ("Reports", self.show_reports), ("Settings", self.show_settings),
            ("Logout", self.logout),
        ]:
            ctk.CTkButton(sidebar, text=label, width=180, height=42, anchor="w", font=BUTTON_FONT,
                          fg_color="transparent", hover_color=PRIMARY, command=callback).pack(pady=5)
        self.main = ctk.CTkFrame(self.root, fg_color=BG_COLOR, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

    def _clear(self, title):
        for widget in self.main.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.main, text=title, font=TITLE_FONT, text_color=TEXT).pack(anchor="w", padx=40, pady=(30, 5))
        ctk.CTkLabel(self.main, text=f"Welcome back, {self.username}  |  {date.today().strftime('%B %Y')}", font=NORMAL_FONT,
                     text_color=TEXT_SECONDARY).pack(anchor="w", padx=40, pady=(0, 20))

    def _totals(self):
        month = date.today().strftime("%Y-%m") + "%"
        with self._connection() as conn:
            income = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE username=? AND date LIKE ?", (self.username, month)).fetchone()[0]
            expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE username=? AND date LIKE ?", (self.username, month)).fetchone()[0]
            row = conn.execute("SELECT monthly_budget FROM budget WHERE username=? ORDER BY id DESC LIMIT 1", (self.username,)).fetchone()
        return income, expenses, row[0] if row else 0

    def _card(self, parent, title, amount, color):
        card = ctk.CTkFrame(parent, fg_color=CARD, height=105)
        card.pack(side="left", padx=8, fill="x", expand=True); card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=NORMAL_FONT, text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(18, 1))
        ctk.CTkLabel(card, text=f"₹ {amount:,.2f}", font=CARD_VALUE, text_color=color).pack(anchor="w", padx=16)

    def show_dashboard(self):
        self._clear("Dashboard")
        income, expenses, budget = self._totals()
        health = "Set a monthly budget to start tracking your goal." if not budget else ("Excellent control - you are within budget." if expenses <= budget else "Budget exceeded - reduce non-essential spending.")
        hero = ctk.CTkFrame(self.main, fg_color=PRIMARY, corner_radius=16)
        hero.pack(fill="x", padx=32, pady=(0, 18))
        ctk.CTkLabel(hero, text="Your money, in one clear view", font=("Segoe UI", 23, "bold"), text_color="#082032").pack(anchor="w", padx=24, pady=(18, 2))
        ctk.CTkLabel(hero, text=health, font=NORMAL_FONT, text_color="#082032").pack(anchor="w", padx=24, pady=(0, 18))
        row = ctk.CTkFrame(self.main, fg_color="transparent"); row.pack(fill="x", padx=32)
        self._card(row, "Monthly income", income, SUCCESS)
        self._card(row, "Monthly expenses", expenses, DANGER)
        self._card(row, "Available balance", income - expenses, PRIMARY)
        self._card(row, "Budget left", budget - expenses, WARNING)
        action_row = ctk.CTkFrame(self.main, fg_color="transparent")
        action_row.pack(fill="x", padx=40, pady=(20, 5))
        ctk.CTkLabel(action_row, text="Quick actions", font=HEADING_FONT).pack(side="left")
        ctk.CTkButton(action_row, text="+ Add income", width=140, command=self.show_income).pack(side="right", padx=5)
        ctk.CTkButton(action_row, text="+ Add expense", width=140, fg_color=WARNING, hover_color="#D97706", command=self.show_expense).pack(side="right", padx=5)
        ctk.CTkLabel(self.main, text="Recent transactions", font=HEADING_FONT).pack(anchor="w", padx=40, pady=(30, 10))
        self._history(8)

    def _history(self, limit=25):
        box = ctk.CTkScrollableFrame(self.main, fg_color=CARD)
        box.pack(fill="both", expand=True, padx=40, pady=(0, 25))
        with self._connection() as conn:
            rows = conn.execute("SELECT source detail, amount, date, 'Income' kind FROM income WHERE username=? UNION ALL SELECT category, amount, date, 'Expense' FROM expenses WHERE username=? ORDER BY date DESC LIMIT ?", (self.username, self.username, limit)).fetchall()
        if not rows:
            ctk.CTkLabel(box, text="No transactions yet.", text_color=TEXT_SECONDARY).pack(pady=25)
        for item in rows:
            line = ctk.CTkFrame(box, fg_color="transparent"); line.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(line, text=f"{item['date']}  ·  {item['kind']}: {item['detail']}", font=NORMAL_FONT).pack(side="left")
            sign, color = ("+", SUCCESS) if item['kind'] == "Income" else ("-", DANGER)
            ctk.CTkLabel(line, text=f"{sign} ₹ {item['amount']:,.2f}", text_color=color, font=BUTTON_FONT).pack(side="right")

    def _transaction_form(self, title, options, save):
        self._clear(title)
        form = ctk.CTkFrame(self.main, fg_color=CARD); form.pack(fill="x", padx=40, pady=10)
        amount = ctk.CTkEntry(form, placeholder_text="Amount (₹)", width=320); amount.pack(padx=28, pady=(24, 8))
        category = ctk.CTkComboBox(form, values=options, width=320); category.set(options[0]); category.pack(padx=28, pady=8)
        trans_date = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD", width=320); trans_date.insert(0, date.today().isoformat()); trans_date.pack(padx=28, pady=8)
        ctk.CTkButton(form, text=f"Add {title[:-1] if title.endswith('s') else title}", width=320,
                      command=lambda: save(amount.get(), category.get(), trans_date.get())).pack(padx=28, pady=(8, 24))
        ctk.CTkLabel(self.main, text="Transaction history", font=HEADING_FONT).pack(anchor="w", padx=40, pady=(20, 10))
        self._history()

    def _valid(self, raw_amount, raw_date):
        try:
            amount = float(raw_amount); datetime.strptime(raw_date, "%Y-%m-%d")
            if amount <= 0: raise ValueError
            return amount
        except ValueError:
            messagebox.showerror("Invalid details", "Enter a positive amount and a date in YYYY-MM-DD format.")
            return None

    def show_income(self):
        self._transaction_form("Income", ["Salary", "Freelance", "Business", "Investment", "Other"], self.add_income)

    def show_expense(self):
        self._transaction_form("Expenses", ["Food", "Transport", "Rent", "Bills", "Shopping", "Health", "Entertainment", "Other"], self.add_expense)

    def add_income(self, raw_amount, source, trans_date):
        amount = self._valid(raw_amount, trans_date)
        if amount is not None:
            with self._connection() as conn: conn.execute("INSERT INTO income(username,amount,source,date) VALUES(?,?,?,?)", (self.username, amount, source, trans_date))
            self.show_income()

    def add_expense(self, raw_amount, category, trans_date):
        amount = self._valid(raw_amount, trans_date)
        if amount is not None:
            with self._connection() as conn: conn.execute("INSERT INTO expenses(username,amount,category,date) VALUES(?,?,?,?)", (self.username, amount, category, trans_date))
            self.show_expense()

    def show_budget(self):
        self._clear("Monthly Budget")
        _, spent, budget = self._totals()
        ctk.CTkLabel(self.main, text=f"Current budget: ₹ {budget:,.2f}\nSpent this month: ₹ {spent:,.2f}\nRemaining: ₹ {budget-spent:,.2f}", font=SUBTITLE_FONT, justify="left").pack(anchor="w", padx=40, pady=12)
        entry = ctk.CTkEntry(self.main, placeholder_text="New monthly budget (₹)", width=320); entry.pack(anchor="w", padx=40, pady=12)
        ctk.CTkButton(self.main, text="Save Budget", width=320, command=lambda: self.save_budget(entry.get())).pack(anchor="w", padx=40)

    def save_budget(self, text):
        try:
            amount = float(text)
            if amount < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid budget", "Enter a valid non-negative amount."); return
        with self._connection() as conn:
            conn.execute("DELETE FROM budget WHERE username=?", (self.username,))
            conn.execute("INSERT INTO budget(username,monthly_budget) VALUES(?,?)", (self.username, amount))
        self.show_budget()

    def show_reports(self):
        self._clear("Reports")
        income, expenses, budget = self._totals()
        used = (expenses / budget * 100) if budget else 0
        ctk.CTkLabel(self.main, text=f"This month\n\nIncome: ₹ {income:,.2f}\nExpenses: ₹ {expenses:,.2f}\nSavings: ₹ {income-expenses:,.2f}\nBudget used: {used:.1f}%", font=SUBTITLE_FONT, justify="left").pack(anchor="w", padx=40, pady=12)
        ctk.CTkLabel(self.main, text="Expense categories", font=HEADING_FONT).pack(anchor="w", padx=40, pady=(20, 8))
        box = ctk.CTkScrollableFrame(self.main, fg_color=CARD); box.pack(fill="both", expand=True, padx=40, pady=(0, 25))
        with self._connection() as conn: rows = conn.execute("SELECT category, SUM(amount) total FROM expenses WHERE username=? AND date LIKE ? GROUP BY category ORDER BY total DESC", (self.username, date.today().strftime('%Y-%m') + '%')).fetchall()
        if not rows:
            ctk.CTkLabel(box, text="No expenses this month. Add expenses to unlock the graph.", text_color=TEXT_SECONDARY).pack(pady=25)
            return
        # A pie chart makes the category split easy to understand at a glance.
        chart = FigureCanvasTkAgg(expense_pie_chart(rows), master=box)
        chart.draw()
        chart.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=12)
        ctk.CTkLabel(box, text="Budget vs spending", font=HEADING_FONT).pack(anchor="w", padx=20, pady=(12, 4))
        remaining = max(budget - expenses, 0)
        progress = ctk.CTkProgressBar(box, width=500, progress_color=DANGER)
        progress.pack(anchor="w", padx=20, pady=(0, 4))
        progress.set(min(expenses / budget, 1) if budget else 0)
        ctk.CTkLabel(box, text=f"Spent ₹ {expenses:,.2f} of ₹ {budget:,.2f}  |  Remaining ₹ {remaining:,.2f}", text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 15))

    def show_settings(self):
        self._clear("Settings")
        ctk.CTkLabel(self.main, text="Account settings", font=HEADING_FONT).pack(anchor="w", padx=40, pady=12)
        card = ctk.CTkFrame(self.main, fg_color=CARD); card.pack(fill="x", padx=40, pady=8)
        ctk.CTkLabel(card, text=f"Signed in as  {self.username}", font=SUBTITLE_FONT).pack(anchor="w", padx=25, pady=(25, 10))
        ctk.CTkLabel(card, text="Your financial data stays in the local SQLite database on this computer.", text_color=TEXT_SECONDARY).pack(anchor="w", padx=25, pady=(0, 25))

    def logout(self):
        self.root.destroy()
        from modules.login import LoginPage
        LoginPage()
