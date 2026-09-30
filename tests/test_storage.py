from expense_bot import storage
import pytest
import sqlite3


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