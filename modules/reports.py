from datetime import date
from utils.db import category_totals, fetch_monthly_totals


def monthly_report(username):
    month = date.today().strftime("%Y-%m")
    income, expense = fetch_monthly_totals(username, month)
    return {"income": income, "expenses": expense, "savings": income - expense, "categories": category_totals(username, month)}
