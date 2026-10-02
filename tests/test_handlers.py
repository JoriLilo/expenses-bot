from expense_bot import handlers, storage


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