"""Reusable CRUD helpers for finance records."""
from database.database import connect


def fetch_monthly_totals(username, month_prefix):
    with connect() as conn:
        income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE username=? AND date LIKE ?", (username, month_prefix + "%")).fetchone()[0]
        expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE username=? AND date LIKE ?", (username, month_prefix + "%")).fetchone()[0]
    return float(income), float(expense)


def recent_transactions(username, limit=20):
    with connect() as conn:
        return conn.execute("SELECT source AS label, amount, date, 'Income' AS type FROM income WHERE username=? UNION ALL SELECT category, amount, date, 'Expense' FROM expenses WHERE username=? ORDER BY date DESC LIMIT ?", (username, username, limit)).fetchall()


def category_totals(username, month_prefix):
    with connect() as conn:
        return conn.execute("SELECT category, SUM(amount) AS total FROM expenses WHERE username=? AND date LIKE ? GROUP BY category ORDER BY total DESC", (username, month_prefix + "%")).fetchall()
