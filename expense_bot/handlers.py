from datetime import timezone

from . import storage
from .parser import ParseError, parse_expense


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