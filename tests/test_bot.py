import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from expense_bot import bot, storage

OWNER = 111
STRANGER = 222


class FakeMessage:
    def __init__(self, text=None):
        self.text = text
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


def make_update(user_id, text=None):
    user = None if user_id is None else SimpleNamespace(id=user_id)
    return SimpleNamespace(effective_user=user, message=FakeMessage(text))


def run(handler, update, args=()):
    context = SimpleNamespace(args=list(args))
    asyncio.run(handler(update, context))


@pytest.fixture(autouse=True)
def configured_bot(monkeypatch, tmp_path):
    monkeypatch.setattr(bot, "ALLOWED_USER_ID", OWNER)
    monkeypatch.setattr(bot, "DB_PATH", str(tmp_path / "test.db"))


def test_is_owner_accepts_owner():
    assert bot.is_owner(make_update(OWNER)) is True


def test_is_owner_rejects_stranger():
    assert bot.is_owner(make_update(STRANGER)) is False


def test_is_owner_rejects_update_without_user():
    assert bot.is_owner(make_update(None)) is False


@pytest.mark.parametrize("name", [
    "on_text", "on_undo", "on_today", "on_wallet",
    "on_in", "on_recent", "on_undoin", "on_undowallet", "on_week",
])
def test_stranger_gets_no_reply_and_touches_no_data(name):
    update = make_update(STRANGER, "coffee 150")

    run(getattr(bot, name), update, args=["100"])

    assert update.message.replies == []
    assert not Path(bot.DB_PATH).exists()


def test_owner_can_log_an_expense_through_the_bot():
    update = make_update(OWNER, "coffee 150 food")

    run(bot.on_text, update)

    assert update.message.replies == ["Logged: coffee - 150 lek [food]"]
    conn = storage.connect(bot.DB_PATH)
    assert len(storage.list_expenses(conn)) == 1


def test_wallet_command_passes_its_arguments_to_the_handler():
    update = make_update(OWNER)

    run(bot.on_wallet, update, args=["4200"])

    assert "Baseline saved: 4200" in update.message.replies[0]


def test_wallet_without_arguments_asks_for_an_amount():
    update = make_update(OWNER)

    run(bot.on_wallet, update, args=[])

    assert update.message.replies[0].startswith("Couldn't read that:")