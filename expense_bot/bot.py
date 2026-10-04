import os
import logging 
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from . import handlers, storage
from datetime import datetime
from zoneinfo import ZoneInfo


load_dotenv()
ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])
DB_PATH = os.environ.get("DB_PATH", "expenses.db")
TIRANA = ZoneInfo("Europe/Tirane")

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    # httpx logs full request URLs at INFO, and Telegram URLs contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def is_owner(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == ALLOWED_USER_ID


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None or update.message.text is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.log_message(conn, update.message.text)
    finally:
        conn.close()

    await update.message.reply_text(reply)


async def on_undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.undo_message(conn)
    finally:
        conn.close()

    await update.message.reply_text(reply)

async def on_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.today_message(conn, datetime.now(TIRANA))
    finally:
        conn.close()

    await update.message.reply_text(reply)


async def on_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.wallet_message(conn, " ".join(context.args))
    finally:
        conn.close()

    await update.message.reply_text(reply)


async def on_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.in_message(conn, " ".join(context.args))
    finally:
        conn.close()

    await update.message.reply_text(reply)

async def on_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.recent_message(conn, datetime.now(TIRANA))
    finally:
        conn.close()

    await update.message.reply_text(reply)


async def on_undoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.undo_in_message(conn)
    finally:
        conn.close()

    await update.message.reply_text(reply)


async def on_undowallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.undo_wallet_message(conn)
    finally:
        conn.close()

    await update.message.reply_text(reply)    

async def on_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update) or update.message is None:
        return

    conn = storage.connect(DB_PATH)
    try:
        reply = handlers.week_message(conn, datetime.now(TIRANA))
    finally:
        conn.close()

    await update.message.reply_text(reply)



async def on_error(update, context):
    logger.error("Unhandled exception while handling an update", exc_info=context.error)
    message = getattr(update, "effective_message", None)
    if message is not None and is_owner(update):
        await message.reply_text("Something went wrong. It's been logged.")

def main():
    setup_logging()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CommandHandler("undo", on_undo))
    app.add_handler(CommandHandler("today", on_today))
    app.add_handler(CommandHandler("wallet", on_wallet))
    app.add_handler(CommandHandler("in", on_in))
    app.add_handler(CommandHandler("recent", on_recent))
    app.add_handler(CommandHandler("undoin", on_undoin))
    app.add_handler(CommandHandler("undowallet", on_undowallet))
    app.add_handler(CommandHandler("week", on_week))
    app.add_error_handler(on_error)
    app.run_polling()


if __name__ == "__main__":
    main()