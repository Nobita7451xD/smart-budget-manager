import hashlib
from database.database import connect


def change_password(username, current_password, new_password):
    """Change a password after confirming the existing password."""
    with connect() as conn:
        row = conn.execute("SELECT password FROM users WHERE username=?", (username,)).fetchone()
        if not row or row[0] != current_password:
            return False
        conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
    return True
