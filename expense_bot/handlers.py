from datetime import datetime, timezone

from . import storage
from .parser import ParseError, parse_amount, parse_expense


def log_message(conn, text):
    try:
        parsed = parse_expense(text)
    except ParseError as e:
        return f"Couldn't log that: {e}"

    storage.add_expense(conn, parsed.item, parsed.amount, parsed.category)
    return f"Logged: {parsed.item} - {parsed.amount} lek [{parsed.category}]"


def undo_message(conn):
    removed = storage.delete_last(conn)
    if removed is None:
        return "Nothing to undo."
    return f"Removed: {removed['item']} - {removed['amount']} lek [{removed['category']}]"


def _expected_wallet(conn):
    """Cash the wallet should hold now, or None if there's no baseline yet."""
    previous = storage.latest_checkpoint(conn)
    if previous is None:
        return None
    since = datetime.fromisoformat(previous["created_at"])
    spent = storage.total_since(conn, since)
    received = storage.total_cash_in_since(conn, since)
    return previous["amount"] + received - spent


def today_message(conn, now):
    local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = local_midnight.astimezone(timezone.utc)

    totals = storage.totals_by_category_since(conn, start_utc)
    if not totals:
        lines = ["Nothing logged today."]
    else:
        lines = [f"{category}: {amount} lek" for category, amount in totals.items()]
        lines.append(f"Total: {sum(totals.values())} lek")

    expected = _expected_wallet(conn)
    if expected is not None:
        lines.append(f"Wallet: {expected} lek left (expected)")

    return "\n".join(lines)


def in_message(conn, text):
    try:
        amount = parse_amount(text)
    except ParseError as e:
        return f"Couldn't log that: {e}"

    storage.add_cash_in(conn, amount)
    return f"Cash in: {amount} lek"


def wallet_message(conn, text, now=None):
    try:
        actual = parse_amount(text, allow_zero=True)
    except ParseError as e:
        return f"Couldn't read that: {e}"

    if now is None:
        now = datetime.now(timezone.utc)

    expected = _expected_wallet(conn)
    if expected is None:
        storage.set_checkpoint(conn, actual, now)
        return f"Baseline saved: {actual} lek"


    gap = expected - actual

    storage.set_checkpoint(conn, actual, now)

    if gap == 0:
        return f"Matches. Expected {expected} lek, actual {actual} lek."
    if gap > 0:
        return f"Missing {gap} lek. Expected {expected} lek, actual {actual} lek."
    return f"{-gap} lek more than expected. Expected {expected} lek, actual {actual} lek."


def undo_in_message(conn):
    removed = storage.delete_last_cash_in(conn)
    if removed is None:
        return "No cash-in to undo."
    return f"Removed cash in: {removed['amount']} lek"


def undo_wallet_message(conn):
    removed = storage.delete_last_checkpoint(conn)
    if removed is None:
        return "No wallet count to undo."

    previous = storage.latest_checkpoint(conn)
    if previous is None:
        return (
            f"Removed wallet count: {removed['amount']} lek. "
            f"No baseline left; your next /wallet starts a new one."
        )
    return (
        f"Removed wallet count: {removed['amount']} lek. "
        f"Last count is now {previous['amount']} lek."
    )


def recent_message(conn, now):
    rows = storage.recent_activity(conn)
    if not rows:
        return "Nothing logged yet."

    lines = []
    for row in rows:
        when = datetime.fromisoformat(row["created_at"]).astimezone(now.tzinfo)
        stamp = when.strftime("%d %b %H:%M")
        if row["kind"] == "expense":
            lines.append(f"{stamp}  -{row['amount']} {row['label']}")
        elif row["kind"] == "cash_in":
            note = f" ({row['label']})" if row["label"] else ""
            lines.append(f"{stamp}  +{row['amount']} cash in{note}")
        else:
            lines.append(f"{stamp}  = {row['amount']} wallet count")
    return "\n".join(lines)
