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