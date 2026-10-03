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


def test_totals_by_category_since():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.add_expense(conn, "lunch", 600, "food", created_at=now)
    storage.add_expense(conn, "coffee", 150, "food", created_at=now)
    storage.add_expense(conn, "bus", 40, "transport", created_at=now)
    storage.add_expense(conn, "old", 999, "food", created_at=now - timedelta(days=10))

    result = storage.totals_by_category_since(conn, now - timedelta(days=1))

    assert result == {"food": 750, "transport": 40}


def test_totals_by_category_empty():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    assert storage.totals_by_category_since(conn, now) == {}


def test_totals_by_category_ordered_largest_first():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.add_expense(conn, "snack", 40, "food", created_at=now)
    storage.add_expense(conn, "rent share", 600, "transport", created_at=now)

    result = storage.totals_by_category_since(conn, now - timedelta(days=1))

    assert list(result) == ["transport", "food"]


def test_delete_last_removes_most_recent():
    conn = storage.connect(":memory:")
    storage.add_expense(conn, "a", 100, "other")
    storage.add_expense(conn, "typo", 9999, "other")

    removed = storage.delete_last(conn)

    assert removed["item"] == "typo"
    rows = storage.list_expenses(conn)
    assert len(rows) == 1
    assert rows[0]["item"] == "a"


def test_delete_last_on_empty_returns_none():
    conn = storage.connect(":memory:")
    assert storage.delete_last(conn) is None    


def test_set_and_get_checkpoint():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.set_checkpoint(conn, 4200, created_at=now)

    cp = storage.latest_checkpoint(conn)

    assert cp["amount"] == 4200
    assert cp["created_at"] == now.isoformat()


def test_latest_checkpoint_returns_most_recent():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.set_checkpoint(conn, 4200, created_at=now - timedelta(days=3))
    storage.set_checkpoint(conn, 3100, created_at=now)

    assert storage.latest_checkpoint(conn)["amount"] == 3100


def test_latest_checkpoint_empty_returns_none():
    conn = storage.connect(":memory:")
    assert storage.latest_checkpoint(conn) is None


def test_checkpoint_rejects_negative():
    conn = storage.connect(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        storage.set_checkpoint(conn, -1, created_at=datetime.now(timezone.utc))


def test_checkpoint_allows_zero():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 0)
    assert storage.latest_checkpoint(conn)["amount"] == 0    


def test_add_cash_in_and_total():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.add_cash_in(conn, 5000, "salary", created_at=now)
    storage.add_cash_in(conn, 1000, created_at=now)

    assert storage.total_cash_in_since(conn, now - timedelta(days=1)) == 6000


def test_cash_in_since_respects_window():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.add_cash_in(conn, 9999, "old", created_at=now - timedelta(days=10))
    storage.add_cash_in(conn, 500, "recent", created_at=now)

    assert storage.total_cash_in_since(conn, now - timedelta(days=1)) == 500


def test_cash_in_empty_returns_zero():
    conn = storage.connect(":memory:")
    assert storage.total_cash_in_since(conn, datetime.now(timezone.utc)) == 0


def test_cash_in_rejects_zero_and_negative():
    conn = storage.connect(":memory:")
    with pytest.raises(sqlite3.IntegrityError):
        storage.add_cash_in(conn, 0)
    with pytest.raises(sqlite3.IntegrityError):
        storage.add_cash_in(conn, -5)


def test_delete_last_cash_in_removes_most_recent():
    conn = storage.connect(":memory:")
    storage.add_cash_in(conn, 500)
    storage.add_cash_in(conn, 5000)

    removed = storage.delete_last_cash_in(conn)

    assert removed["amount"] == 5000
    assert storage.total_cash_in_since(conn, datetime(2000, 1, 1, tzinfo=timezone.utc)) == 500


def test_delete_last_cash_in_empty_returns_none():
    conn = storage.connect(":memory:")
    assert storage.delete_last_cash_in(conn) is None


def test_delete_last_checkpoint_reverts_to_previous():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.set_checkpoint(conn, 5000, created_at=now - timedelta(days=1))
    storage.set_checkpoint(conn, 4200, created_at=now)

    removed = storage.delete_last_checkpoint(conn)

    assert removed["amount"] == 4200
    assert storage.latest_checkpoint(conn)["amount"] == 5000


def test_delete_last_checkpoint_empty_returns_none():
    conn = storage.connect(":memory:")
    assert storage.delete_last_checkpoint(conn) is None


def test_recent_activity_merges_all_kinds_newest_first():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    storage.set_checkpoint(conn, 5000, created_at=now - timedelta(hours=3))
    storage.add_expense(conn, "coffee", 150, "food", created_at=now - timedelta(hours=2))
    storage.add_cash_in(conn, 1000, "salary", created_at=now - timedelta(hours=1))

    rows = storage.recent_activity(conn)

    assert [r["kind"] for r in rows] == ["cash_in", "expense", "wallet"]
    assert [r["amount"] for r in rows] == [1000, 150, 5000]


def test_recent_activity_respects_limit():
    conn = storage.connect(":memory:")
    now = datetime.now(timezone.utc)
    for i in range(5):
        storage.add_expense(conn, f"item{i}", 10, "other", created_at=now + timedelta(minutes=i))

    rows = storage.recent_activity(conn, limit=3)

    assert [r["label"] for r in rows] == ["item4", "item3", "item2"]       