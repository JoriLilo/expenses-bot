import asyncio
import logging
from types import SimpleNamespace

import pytest

from expense_bot import bot

OWNER = 111
STRANGER = 222


class FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


def make_update(user_id):
    message = FakeMessage()
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        message=message,
        effective_message=message,
    )


def run_error_handler(update, error):
    asyncio.run(bot.on_error(update, SimpleNamespace(error=error)))


@pytest.fixture(autouse=True)
def configured_bot(monkeypatch):
    monkeypatch.setattr(bot, "ALLOWED_USER_ID", OWNER)


def test_error_handler_logs_the_exception_and_tells_the_owner(caplog):
    update = make_update(OWNER)
    error = RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        run_error_handler(update, error)

    assert update.effective_message.replies == ["Something went wrong. It's been logged."]
    assert any(r.exc_info and r.exc_info[1] is error for r in caplog.records)


def test_error_handler_stays_silent_to_strangers_but_still_logs(caplog):
    update = make_update(STRANGER)

    with caplog.at_level(logging.ERROR):
        run_error_handler(update, RuntimeError("boom"))

    assert update.effective_message.replies == []
    assert caplog.records


def test_error_handler_survives_an_error_with_no_update(caplog):
    with caplog.at_level(logging.ERROR):
        run_error_handler(None, RuntimeError("boom"))

    assert caplog.records


def test_logging_setup_keeps_httpx_info_logs_out():
    bot.setup_logging()

    httpx_logger = logging.getLogger("httpx")
    assert not httpx_logger.isEnabledFor(logging.INFO)
    assert httpx_logger.isEnabledFor(logging.WARNING)