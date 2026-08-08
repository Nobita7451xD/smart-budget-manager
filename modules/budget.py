from database.database import connect


def get_budget(username):
    with connect() as conn:
        row = conn.execute("SELECT monthly_budget FROM budget WHERE username=? ORDER BY id DESC LIMIT 1", (username,)).fetchone()
    return float(row[0]) if row else 0.0


def save_budget(username, amount):
    with connect() as conn:
        conn.execute("DELETE FROM budget WHERE username=?", (username,))
        conn.execute("INSERT INTO budget(username, monthly_budget) VALUES(?, ?)", (username, float(amount)))
