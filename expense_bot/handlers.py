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


def today_message(conn, now):
    local_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = local_midnight.astimezone(timezone.utc)

    totals = storage.totals_by_category_since(conn, start_utc)
    if not totals:
        return "Nothing logged today."

    lines = [f"{category}: {amount} lek" for category, amount in totals.items()]
    lines.append(f"Total: {sum(totals.values())} lek")
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

    previous = storage.latest_checkpoint(conn)
    if previous is None:
        storage.set_checkpoint(conn, actual, now)
        return f"Baseline saved: {actual} lek"

    since = datetime.fromisoformat(previous["created_at"])
    spent = storage.total_since(conn, since)
    received = storage.total_cash_in_since(conn, since)
    expected = previous["amount"] + received - spent
    gap = expected - actual

    storage.set_checkpoint(conn, actual, now)

    if gap == 0:
        return (
            f"Matches. Expected {expected} lek, actual {actual} lek."
        )
    if gap > 0:
        return (
            f"Missing {gap} lek. Expected {expected} lek, actual {actual} lek."
        )
    return (
        f"{-gap} lek more than expected. Expected {expected} lek, actual {actual} lek."
    )