import sqlite3


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount > 0),
            category TEXT NOT NULL
        )
    """)
    return conn


def add_expense(conn, item, amount, category):
    conn.execute(
        "INSERT INTO expenses (item, amount, category) VALUES (?, ?, ?)",
        (item, amount, category),
    )
    conn.commit()


def list_expenses(conn):
    cursor = conn.execute("SELECT * FROM expenses")
    return cursor.fetchall()
