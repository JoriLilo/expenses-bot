FROM python:3.14-slim

LABEL org.opencontainers.image.source="https://github.com/JoriLilo/expenses-bot"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY expense_bot ./expense_bot

RUN useradd --create-home --uid 1000 app \
    && mkdir /data \
    && chown app:app /data
USER app

ENV DB_PATH=/data/expenses.db
VOLUME /data

CMD ["python", "-m", "expense_bot.bot"]