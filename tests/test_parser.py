import pytest
from expense_bot.parser import ParseError, parse_amount, parse_expense

def test_basic():
    p = parse_expense("coffee 150")
    assert p.item == "coffee"
    assert p.amount == 150
    assert p.category == "other"

def test_with_category():
    p = parse_expense("lunch 600 food")
    assert p.item == "lunch"
    assert p.amount == 600
    assert p.category == "food"

def test_multiword_item():
    p = parse_expense("bus ticket 40 transport")
    assert p.item == "bus ticket"
    assert p.amount == 40
    assert p.category == "transport"

def test_no_amount_raises():
    with pytest.raises(ParseError):
        parse_expense("coffee")

def test_zero_raises():
    with pytest.raises(ParseError):
        parse_expense("coffee 0")


def test_two_numbers_raises():
    with pytest.raises(ParseError):
        parse_expense("coffee 10 20")


def test_extra_words_raises():
    with pytest.raises(ParseError):
        parse_expense("coffee 150 food extra")


def test_amount_first_raises():
    with pytest.raises(ParseError):
        parse_expense("150 coffee")

def test_negative_raises_clear_message():
    with pytest.raises(ParseError, match="whole number"):
        parse_expense("coffee -50")


def test_decimal_raises_clear_message():
    with pytest.raises(ParseError, match="whole number"):
        parse_expense("coffee 12.5")


def test_comma_raises_clear_message():
    with pytest.raises(ParseError, match="whole number"):
        parse_expense("coffee 1,500")     

def test_case_is_normalized():
    p = parse_expense("Coffee 150 FOOD")
    assert p.item == "coffee"
    assert p.category == "food"   


def test_parse_amount_basic():
    assert parse_amount("4200") == 4200


def test_parse_amount_strips_whitespace():
    assert parse_amount("  4200 ") == 4200


def test_parse_amount_empty_raises():
    with pytest.raises(ParseError, match="No amount"):
        parse_amount("")


def test_parse_amount_two_words_raises():
    with pytest.raises(ParseError):
        parse_amount("100 200")


@pytest.mark.parametrize("bad", ["abc", "-50", "12.5", "1,500"])
def test_parse_amount_rejects_non_whole_numbers(bad):
    with pytest.raises(ParseError, match="whole number"):
        parse_amount(bad)


def test_parse_amount_zero_rejected_by_default():
    with pytest.raises(ParseError, match="positive"):
        parse_amount("0")


def test_parse_amount_zero_allowed_when_asked():
    assert parse_amount("0", allow_zero=True) == 0