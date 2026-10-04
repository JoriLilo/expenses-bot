![CI](https://github.com/JoriLilo/expenses-bot/actions/workflows/ci.yml/badge.svg)

# expenses-bot

A Telegram bot that logs my cash spending from plain chat messages and tells me when my wallet doesn't add up.

## The problem

I spent cash and couldn't say where it went. Banking apps cover cards; nothing covered the notes in my wallet. This bot logs each purchase as a one-line message, and a wallet check compares the cash I *should* have with the cash I actually count, so missing money shows up as a number instead of a feeling.

## What it does

| Message | Effect |
|---|---|
| `coffee 150 food` | Logs an expense: item words, a whole-number amount in lek, and an optional one-word category (default `other`) |
| `/undo` | Removes the last expense |
| `/today` | Spending since local midnight, by category, largest first, plus the expected cash left in the wallet |
| `/in 5000` | Records cash received |
| `/undoin` | Removes the last cash-in |
| `/wallet 4200` | Counts the wallet and reconciles it against the log (see below) |
| `/undowallet` | Removes the last wallet count, so the previous count becomes the baseline again |
| `/recent` | The last 10 entries of every kind, newest first, in local time |
| `/week` | Spending over the last 7 local days by category, with the total compared to the 7 days before |

Bad input is rejected with a specific message and stores nothing: `coffee 12.5` and `coffee 1,500` ask for a whole number, and a bare `/wallet` asks for an amount.

## The wallet check

```
expected = last wallet count + cash received since − expenses logged since
gap      = expected − counted
```

- **Gap > 0:** I spent or lost cash I didn't log. This is the "where did it go" answer.
- **Gap < 0:** I have more cash than expected, so I forgot to log money coming in.
- **First ever `/wallet`:** there is nothing to compare against, so it only saves a baseline.
- After every check, the count I typed becomes the new baseline, so one mistake never contaminates later checks. A wrong count can be removed with `/undowallet` and entered again.

## How it's built

```
expense_bot/
  parser.py    text -> validated values (raises ParseError)
  storage.py   SQLite; the only module that contains SQL
  handlers.py  connection + text -> reply string; no Telegram code
  bot.py       thin Telegram wiring: owner check, open DB, call handler, reply
  backup.py    consistent SQLite snapshot into backups/
tests/         pytest suite covering all five modules
```

The handlers return plain strings, so the business logic is tested without a network connection or a Telegram account. The code was written test-first: each behavior began as a failing test, including the edge cases (empty tables, the local-midnight boundary, entries before a checkpoint being ignored, wrong input storing nothing).

Every push to `main` runs GitHub Actions: the test suite first, then a build of the Docker image with a smoke test of the result.

## Security

- Only one Telegram user ID is allowed. Anyone else gets no reply, and the bot never opens the database for them (tested for every command).
- The bot token and user ID come from environment variables. `.env` is git-ignored and excluded from the Docker build context, and the image contains no secrets.
- Logging keeps the `httpx` logger at WARNING, because its INFO logs print request URLs and Telegram URLs contain the bot token. A test pins this.
- An unexpected exception is logged with a full traceback and the owner gets "Something went wrong" instead of silence.

## Run it

You need Python 3.14 (what CI and the Docker image use), a bot token from [@BotFather](https://t.me/BotFather), and your numeric Telegram user ID.

```bash
git clone https://github.com/JoriLilo/expenses-bot.git
cd expenses-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then fill in both values
python -m expense_bot.bot
```

| Variable | Required | Meaning |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | Token from BotFather |
| `ALLOWED_USER_ID` | yes | The only Telegram user the bot answers |
| `DB_PATH` | no | SQLite file, default `expenses.db` |
| `BACKUP_DIR` | no | Backup folder, default `backups` |

Run the tests with `python -m pytest`.

### Docker

```bash
docker build -t expenses-bot .
docker run --rm --env-file .env -v expenses-data:/data expenses-bot
```

The database lives at `/data/expenses.db` inside the container, on a named volume, so it survives restarts and image rebuilds. Secrets are passed at run time and never copied into the image. Run only one instance per token: two programs polling Telegram with the same token will fight over updates.

### Backups

```bash
python -m expense_bot.backup
```

This writes a timestamped copy to `backups/` using SQLite's backup API, so the snapshot is consistent even if the bot is writing at that moment. Backups are git-ignored because they contain real data. They sit next to the database, so copy them somewhere else occasionally.

## Design decisions and limits

- **Cash only.** A card purchase logged here would never leave the wallet and would show up as phantom missing cash, so the wallet check would stop meaning anything. Card spending belongs in a separate tracker.
- **Whole numbers only.** Amounts are integers in lek, and the parser rejects decimals and thousands separators instead of guessing.
- **Undo removes only the latest entry.** Editing arbitrary history would make the numbers untrustworthy. Because every `/wallet` count resets the baseline, an old mistake can only distort the one interval it happened in.
- **Single user.** The bot is built for one person's wallet.
- **Not hosted.** It runs while the process or container runs, which today means on my own machine.
- **Timestamps** are stored in UTC and converted to Tirana time for display and for the "today" boundary.