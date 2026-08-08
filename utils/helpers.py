from datetime import datetime


def format_currency(amount):
    return f"₹ {float(amount):,.2f}"


def validate_transaction(amount, transaction_date):
    try:
        value = float(amount)
        datetime.strptime(transaction_date, "%Y-%m-%d")
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def today_iso():
    return datetime.now().date().isoformat()
