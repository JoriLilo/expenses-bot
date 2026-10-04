from expense_bot import handlers, storage
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TIRANA = ZoneInfo("Europe/Tirane")

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


BASE = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_wallet_first_check_saves_baseline_only():
    conn = storage.connect(":memory:")

    reply = handlers.wallet_message(conn, "4200", now=BASE)

    assert "Baseline saved: 4200" in reply
    assert storage.latest_checkpoint(conn)["amount"] == 4200


def test_wallet_accepts_zero():
    conn = storage.connect(":memory:")
    handlers.wallet_message(conn, "0", now=BASE)
    assert storage.latest_checkpoint(conn)["amount"] == 0


def test_wallet_exact_match():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.add_expense(conn, "lunch", 200, "food", created_at=BASE + timedelta(hours=1))
    storage.add_cash_in(conn, 1000, created_at=BASE + timedelta(hours=2))

    reply = handlers.wallet_message(conn, "5800", now=BASE + timedelta(hours=3))

    assert "Matches" in reply


def test_wallet_positive_gap_means_unlogged_spending():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.add_expense(conn, "lunch", 200, "food", created_at=BASE + timedelta(hours=1))

    reply = handlers.wallet_message(conn, "4500", now=BASE + timedelta(hours=3))

    assert "Missing 300 lek" in reply


def test_wallet_negative_gap_means_unlogged_cash_in():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)

    reply = handlers.wallet_message(conn, "5500", now=BASE + timedelta(hours=3))

    assert "500 lek more than expected" in reply


def test_wallet_ignores_entries_before_checkpoint():
    conn = storage.connect(":memory:")
    storage.add_expense(conn, "old", 999, "food", created_at=BASE - timedelta(hours=1))
    storage.add_cash_in(conn, 777, created_at=BASE - timedelta(hours=2))
    storage.set_checkpoint(conn, 5000, created_at=BASE)

    reply = handlers.wallet_message(conn, "5000", now=BASE + timedelta(hours=3))

    assert "Matches" in reply


def test_wallet_each_check_becomes_new_baseline():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.add_expense(conn, "lunch", 200, "food", created_at=BASE + timedelta(hours=1))
    handlers.wallet_message(conn, "4800", now=BASE + timedelta(hours=2))
    storage.add_expense(conn, "coffee", 100, "food", created_at=BASE + timedelta(hours=3))

    reply = handlers.wallet_message(conn, "4700", now=BASE + timedelta(hours=4))

    assert "Matches" in reply
    assert storage.latest_checkpoint(conn)["amount"] == 4700


def test_wallet_bad_input_stores_nothing():
    conn = storage.connect(":memory:")
    for bad in ["abc", "-5", "12.5", ""]:
        reply = handlers.wallet_message(conn, bad, now=BASE)
        assert reply.startswith("Couldn't read that:")
    assert storage.latest_checkpoint(conn) is None


def test_in_stores_and_confirms():
    conn = storage.connect(":memory:")

    reply = handlers.in_message(conn, "5000")

    assert reply == "Cash in: 5000 lek"
    assert storage.total_cash_in_since(conn, EPOCH) == 5000


def test_in_bad_input_stores_nothing():
    conn = storage.connect(":memory:")
    for bad in ["abc", "0", "-5", ""]:
        reply = handlers.in_message(conn, bad)
        assert reply.startswith("Couldn't log that:")
    assert storage.total_cash_in_since(conn, EPOCH) == 0

def test_today_shows_expected_wallet_since_checkpoint():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 1, 9, 0, tzinfo=TIRANA)
    storage.set_checkpoint(conn, 5000, created_at=datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc))
    storage.add_cash_in(conn, 1000, created_at=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc))
    # yesterday: not in today's list, but still leaves the wallet
    storage.add_expense(conn, "dinner", 300, "food",
                        created_at=datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc))
    # today
    storage.add_expense(conn, "coffee", 150, "food",
                        created_at=datetime(2026, 10, 1, 6, 0, tzinfo=timezone.utc))

    reply = handlers.today_message(conn, now)

    assert reply == "food: 150 lek\nTotal: 150 lek\nWallet: 5550 lek left (expected)"


def test_today_empty_still_shows_wallet():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 1, 9, 0, tzinfo=TIRANA)
    storage.set_checkpoint(conn, 5000, created_at=datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc))

    reply = handlers.today_message(conn, now)

    assert reply == "Nothing logged today.\nWallet: 5000 lek left (expected)"


def test_undo_in_removes_last_and_says_what():
    conn = storage.connect(":memory:")
    handlers.in_message(conn, "500")
    handlers.in_message(conn, "5000")

    reply = handlers.undo_in_message(conn)

    assert reply == "Removed cash in: 5000 lek"


def test_undo_in_on_empty():
    conn = storage.connect(":memory:")
    assert handlers.undo_in_message(conn) == "No cash-in to undo."


def test_undo_wallet_reverts_to_previous_count():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.set_checkpoint(conn, 4200, created_at=BASE + timedelta(hours=1))

    reply = handlers.undo_wallet_message(conn)

    assert reply == "Removed wallet count: 4200 lek. Last count is now 5000 lek."


def test_undo_wallet_first_count_leaves_no_baseline():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 4200, created_at=BASE)

    reply = handlers.undo_wallet_message(conn)

    assert "No baseline left" in reply
    assert storage.latest_checkpoint(conn) is None


def test_undo_wallet_on_empty():
    conn = storage.connect(":memory:")
    assert handlers.undo_wallet_message(conn) == "No wallet count to undo."


def test_wrong_wallet_count_can_be_undone_and_redone():
    conn = storage.connect(":memory:")
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.add_expense(conn, "lunch", 200, "food", created_at=BASE + timedelta(hours=1))
    # typo: meant 4800
    assert "Missing 600 lek" in handlers.wallet_message(conn, "4200", now=BASE + timedelta(hours=2))

    handlers.undo_wallet_message(conn)
    reply = handlers.wallet_message(conn, "4800", now=BASE + timedelta(hours=3))

    assert "Matches" in reply
    assert storage.latest_checkpoint(conn)["amount"] == 4800


def test_recent_lists_all_kinds_newest_first_in_local_time():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 3, 20, 0, tzinfo=TIRANA)
    storage.set_checkpoint(conn, 5000, created_at=BASE)
    storage.add_expense(conn, "coffee", 150, "food", created_at=BASE + timedelta(hours=1))
    storage.add_cash_in(conn, 1000, "salary", created_at=BASE + timedelta(hours=2))

    reply = handlers.recent_message(conn, now)

    assert reply == (
        "03 Oct 16:00  +1000 cash in (salary)\n"
        "03 Oct 15:00  -150 coffee\n"
        "03 Oct 14:00  = 5000 wallet count"
    )


def test_recent_empty():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 3, 20, 0, tzinfo=TIRANA)
    assert handlers.recent_message(conn, now) == "Nothing logged yet."    


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_week_groups_by_category_and_compares_with_previous_week():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 4, 15, 0, tzinfo=TIRANA)  # window starts Sep 28 00:00 local
    # this week
    storage.add_expense(conn, "groceries", 1000, "food", created_at=utc(2026, 10, 3, 10, 0))
    storage.add_expense(conn, "lunch", 200, "food", created_at=utc(2026, 10, 4, 6, 0))
    storage.add_expense(conn, "bus", 500, "transport", created_at=utc(2026, 9, 27, 22, 0))  # exactly local midnight
    # previous 7 days
    storage.add_expense(conn, "shoes", 1000, "other", created_at=utc(2026, 9, 25, 10, 0))
    storage.add_expense(conn, "snack", 300, "food", created_at=utc(2026, 9, 27, 21, 59))  # one minute too early
    # older than both windows
    storage.add_expense(conn, "ancient", 999, "other", created_at=utc(2026, 9, 20, 21, 59))

    reply = handlers.week_message(conn, now)

    assert reply == (
        "food: 1200 lek\n"
        "transport: 500 lek\n"
        "Total: 1700 lek\n"
        "Previous 7 days: 1300 lek (+400)"
    )


def test_week_empty():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 4, 15, 0, tzinfo=TIRANA)

    assert handlers.week_message(conn, now) == "Nothing logged in the last 7 days."


def test_week_with_nothing_in_previous_week():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 4, 15, 0, tzinfo=TIRANA)
    storage.add_expense(conn, "bus", 500, "transport", created_at=utc(2026, 10, 3, 10, 0))

    reply = handlers.week_message(conn, now)

    assert reply == "transport: 500 lek\nTotal: 500 lek\nPrevious 7 days: nothing logged"


def test_week_with_nothing_this_week_but_something_before():
    conn = storage.connect(":memory:")
    now = datetime(2026, 10, 4, 15, 0, tzinfo=TIRANA)
    storage.add_expense(conn, "shoes", 1300, "other", created_at=utc(2026, 9, 25, 10, 0))

    reply = handlers.week_message(conn, now)

    assert reply == "Nothing logged in the last 7 days.\nPrevious 7 days: 1300 lek (-1300)"


def test_week_starts_at_local_midnight_even_across_a_clock_change():
    conn = storage.connect(":memory:")
    # Albania moves its clocks on Oct 25, 2026. On Oct 28 the offset is +01:00,
    # but the window starts on Oct 22, local midnight, which was still +02:00.
    now = datetime(2026, 10, 28, 12, 0, tzinfo=TIRANA)
    storage.add_expense(conn, "inside", 100, "food", created_at=utc(2026, 10, 21, 22, 0))
    storage.add_expense(conn, "outside", 50, "food", created_at=utc(2026, 10, 21, 21, 59))

    reply = handlers.week_message(conn, now)

    assert reply == "food: 100 lek\nTotal: 100 lek\nPrevious 7 days: 50 lek (+50)"    