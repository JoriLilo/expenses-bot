import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


def backup_database(db_path, backup_dir, now=None):
    if now is None:
        now = datetime.now(timezone.utc)

    db_path = Path(db_path)
    if not db_path.exists():
        # sqlite3.connect would silently create an empty database here.
        raise FileNotFoundError(f"No database at {db_path}")

    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"expenses-{now.strftime('%Y%m%dT%H%M%SZ')}.db"

    source = sqlite3.connect(db_path)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return destination


def main():
    load_dotenv()
    db_path = os.environ.get("DB_PATH", "expenses.db")
    backup_dir = os.environ.get("BACKUP_DIR", "backups")
    print(f"Backed up to {backup_database(db_path, backup_dir)}")


if __name__ == "__main__":
    main()