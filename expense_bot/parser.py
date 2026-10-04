from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedExpense:
    item: str
    amount: int
    category: str


class ParseError(ValueError):
    pass


def parse_expense(text):
    text = text.strip().lower()
    tokens = text.split()

    positions = [i for i, word in enumerate(tokens) if looks_like_number(word)]
    if len(positions) > 1:
        raise ParseError("Multiple amounts found. Try: coffee 150 food")
    if len(positions) == 0:
        raise ParseError("No amount found. Try: coffee 150")

    if not tokens[positions[0]].isdecimal():
        raise ParseError("Amount must be a whole number. Try: coffee 150")

    amount = int(tokens[positions[0]])
    if amount <= 0:
        raise ParseError("Amount must be positive.")

    if positions[0] == 0:
        raise ParseError("Amount cannot be the first word. Try: coffee 150")
    item = " ".join(tokens[:positions[0]])

    category_tokens = tokens[positions[0] + 1:]
    if len(category_tokens) > 1:
        raise ParseError(
            f"Too many words after amount: {' '.join(category_tokens)}. "
            "Use a single category word."
        )
    category = category_tokens[0] if category_tokens else "other"

    return ParsedExpense(item, amount, category)


def looks_like_number(word):
    word = word.replace(",", "")
    word = word.replace(".", "")
    word = word.replace("-", "")
    word = word.replace("+", "")
    return word.isdecimal()

def parse_amount(text, allow_zero=False):
    text = text.strip()
    if not text:
        raise ParseError("No amount provided. Try 150")

    if not text.isdecimal():
        raise ParseError("Amount must be a whole number. Try 150")
    amount = int(text)
    if amount == 0 and not allow_zero:
        raise ParseError("Amount must be a positive number.")

    return amount
