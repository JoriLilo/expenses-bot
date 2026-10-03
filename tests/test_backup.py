from datetime import datetime, timezone

import pytest

from expense_bot import storage
from expense_bot.backup import backup_database

NOW = datetime(2026, 10, 4, 0, 15, 6, tzinfo=timezone.utc)


def make_db(tmp_path):
    path = tmp_path / "expenses.db"
    conn = storage.connect(str(path))
    storage.add_expense(conn, "coffee", 150, "food")
    storage.add_cash_in(conn, 5000, "salary")
    storage.set_checkpoint(conn, 4200)
    conn.close()
    return path


def test_backup_contains_all_the_data(tmp_path):
    db = make_db(tmp_path)

    backup = backup_database(db, tmp_path / "backups", now=NOW)

    conn = storage.connect(str(backup))
    assert len(storage.list_expenses(conn)) == 1
    assert storage.latest_checkpoint(conn)["amount"] == 4200
    cash = conn.execute("SELECT amount FROM cash_in").fetchall()
    assert [row["amount"] for row in cash] == [5000]


def test_backup_filename_is_dated_and_sortable(tmp_path):
    db = make_db(tmp_path)

    backup = backup_database(db, tmp_path / "backups", now=NOW)

    assert backup == tmp_path / "backups" / "expenses-20261004T001506Z.db"


def test_backup_creates_the_directory(tmp_path):
    db = make_db(tmp_path)
    target = tmp_path / "deep" / "backups"

    backup_database(db, target, now=NOW)

    assert target.is_dir()


def test_two_backups_never_overwrite_each_other(tmp_path):
    db = make_db(tmp_path)
    later = datetime(2026, 10, 4, 0, 15, 7, tzinfo=timezone.utc)

    backup_database(db, tmp_path / "backups", now=NOW)
    backup_database(db, tmp_path / "backups", now=later)

    assert len(list((tmp_path / "backups").glob("*.db"))) == 2


def test_backup_is_a_snapshot_not_a_link(tmp_path):
    db = make_db(tmp_path)
    backup = backup_database(db, tmp_path / "backups", now=NOW)

    conn = storage.connect(str(db))
    storage.add_expense(conn, "later", 999, "food")
    conn.close()

    assert len(storage.list_expenses(storage.connect(str(backup)))) == 1


def test_missing_database_raises_and_creates_nothing(tmp_path):
    missing = tmp_path / "nope.db"

    with pytest.raises(FileNotFoundError):
        backup_database(missing, tmp_path / "backups", now=NOW)

    assert not missing.exists()
    assert not (tmp_path / "backups").exists()