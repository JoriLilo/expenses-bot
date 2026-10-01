import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from . import handlers, storage

load_dotenv()
ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])
DB_PATH = os.environ.get("DB_PATH", "expenses.db")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.effective_user.id != ALLOWED_USER_ID:
        return

    if update.message is None or update.message.text is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.log_message(conn, update.message.text)
    finally:
        conn.close()

    await update.message.reply_text(reply)


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()