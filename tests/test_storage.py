from expense_bot import storage
import pytest
import sqlite3
from datetime import datetime, timedelta, timezone

def test_add_and_list():
    conn = storage.connect(":memory:")
    storage.add_expense(conn, "coffee", 150, "other")
    rows = storage.list_expenses(conn)
    assert len(rows) == 1
    assert rows[0]["item"] == "coffee"
    assert rows[0]["amount"] == 150

def test_data_persists_after_reconnect(tmp_path):
    db_file = str(tmp_path / "test.db")

    conn = storage.connect(db_file)
    storage.add_expense(conn, "coffee", 150, "other")
    conn.close()

    conn2 = storage.connect(db_file)
    rows = storage.list_expenses(conn2)
    assert len(rows) == 1

def test_rejects_zero_amount():
    conn = storage.connect(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        storage.add_expense(conn, "bad", 0, "other")


def test_total_since_respects_window():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.add_expense(conn, "old", 999, "other", created_at=now - timedelta(days=10))
    storage.add_expense(conn, "coffee", 150, "other", created_at=now)
    assert storage.total_since(conn, now - timedelta(days=1)) == 150

def test_default_timestamp_is_now():
    conn = storage.connect(":memory:")
    before = datetime.now(timezone.utc) - timedelta(minutes=1)
    storage.add_expense(conn, "coffee", 150, "other")
    assert storage.total_since(conn, before) == 150