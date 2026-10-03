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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS wallet_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount >= 0)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cash_in (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount > 0),
            note TEXT
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

def totals_by_category_since(conn, since):
    cursor = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE created_at >= ? GROUP BY category ORDER BY total DESC",
        (since.isoformat(),)
    )
    return {row["category"]: row["total"] for row in cursor.fetchall()}

def delete_last(conn):
    
    cursor = conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        return None
    conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))

    conn.commit()

    return row

def set_checkpoint(conn, amount, created_at=None):
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO wallet_checkpoints (created_at, amount) VALUES (?, ?)",
        (created_at.isoformat(), amount),
    )
    conn.commit()


def latest_checkpoint(conn):
    return conn.execute(
        "SELECT * FROM wallet_checkpoints ORDER BY id DESC LIMIT 1"
    ).fetchone()

def add_cash_in(conn, amount, note=None, created_at=None):
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO cash_in (created_at, amount, note) VALUES (?, ?, ?)",
        (created_at.isoformat(), amount, note),
    )
    conn.commit()

def total_cash_in_since(conn, since):
    row = conn.execute(
        "SELECT SUM(amount) AS total FROM cash_in WHERE created_at > ?",
        (since.isoformat(),),
    ).fetchone()
    return row["total"] if row["total"] is not None else 0