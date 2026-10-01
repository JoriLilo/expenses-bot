from . import storage
from .parser import ParseError, parse_expense


def log_message(conn, text):

    try:
        parsed = parse_expense(text)
    except ParseError as e:
        return f"Couldn't log that: {e}"

    storage.add_expense(conn, parsed.item, parsed.amount, parsed.category)
    return f"Logged: {parsed.item} - {parsed.amount} lek [{parsed.category}]"