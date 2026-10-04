from telegram.ext import CommandHandler, MessageHandler

from expense_bot import bot


class FakeApp:
    def __init__(self):
        self.handlers = []
        self.error_handlers = []
        self.polling_started = False

    def add_handler(self, handler):
        self.handlers.append(handler)

    def add_error_handler(self, callback):
        self.error_handlers.append(callback)

    def run_polling(self):
        self.polling_started = True


class FakeBuilder:
    def __init__(self, app):
        self.app = app

    def token(self, token):
        return self

    def build(self):
        return self.app


def test_main_wires_logging_commands_and_error_handler(monkeypatch):
    app = FakeApp()
    logging_calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setattr(bot.Application, "builder", lambda: FakeBuilder(app))
    monkeypatch.setattr(bot, "setup_logging", lambda: logging_calls.append(True))

    bot.main()

    commands = {
        name
        for handler in app.handlers
        if isinstance(handler, CommandHandler)
        for name in handler.commands
    }
    assert commands == {"undo", "today", "wallet", "in", "recent", "undoin", "undowallet", "week"}
    assert any(isinstance(h, MessageHandler) for h in app.handlers)
    assert app.error_handlers == [bot.on_error]
    assert logging_calls == [True]
    assert app.polling_started