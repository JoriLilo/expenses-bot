from datetime import datetime, timezone
import sqlite3


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount > 0),
            category TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    return conn


def add_expense(conn, item, amount, category, created_at=None):
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO expenses (item, amount, category, created_at) VALUES (?, ?, ?, ?)",
        (item, amount, category, created_at.isoformat()),
    )
    conn.commit()


def list_expenses(conn):
    cursor = conn.execute("SELECT * FROM expenses")
    return cursor.fetchall()

def total_since(conn, since):
    cursor = conn.execute(
        "SELECT SUM(amount) as total FROM expenses WHERE created_at >= ?",
        (since.isoformat(),)
    )
    row = cursor.fetchone()
    return row["total"] if row["total"] is not None else 0