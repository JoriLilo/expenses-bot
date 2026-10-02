from expense_bot import handlers, storage
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TIRANA = ZoneInfo("Europe/Belgrade")

def test_log_message_stores_expense_and_confirms():
    conn = storage.connect(":memory:")
    reply = handlers.log_message(conn, "coffee 150 food")
    assert reply == "Logged: coffee - 150 lek [food]"
    rows = storage.list_expenses(conn)
    assert len(rows) == 1
    assert rows[0]["category"] == "food"


def test_log_message_bad_input_stores_nothing():
    conn = storage.connect(":memory:")
    reply = handlers.log_message(conn, "coffee")
    assert reply.startswith("Couldn't log that:")
    assert storage.list_expenses(conn) == []


def test_undo_removes_last_and_says_what():
    conn = storage.connect(":memory:")
    handlers.log_message(conn, "coffee 150 food")
    handlers.log_message(conn, "lunch 9000 food")

    reply = handlers.undo_message(conn)

    assert reply == "Removed: lunch - 9000 lek [food]"
    rows = storage.list_expenses(conn)
    assert len(rows) == 1
    assert rows[0]["item"] == "coffee"


def test_undo_on_empty():
    conn = storage.connect(":memory:")
    assert handlers.undo_message(conn) == "Nothing to undo."







def test_today_counts_from_local_midnight():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 1, 9, 0, tzinfo=TIRANA)
    # 23:30 on Sep 30 in Tirana: belongs to yesterday
    storage.add_expense(conn, "late snack", 100, "food",
                        created_at=datetime(2026, 9, 30, 21, 30, tzinfo=timezone.utc))
    # 00:15 on Oct 1 in Tirana: belongs to today
    storage.add_expense(conn, "coffee", 150, "food",
                        created_at=datetime(2026, 9, 30, 22, 15, tzinfo=timezone.utc))

    reply = handlers.today_message(conn, now)

    assert reply == "food: 150 lek\nTotal: 150 lek"


def test_today_empty():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 1, 9, 0, tzinfo=TIRANA)
    assert handlers.today_message(conn, now) == "Nothing logged today."