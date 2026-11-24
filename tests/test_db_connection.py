"""US-2: connection factory and default database path."""

import sqlite3
import subprocess
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_SUPPORT = Path("Library/Application Support/budget-app/budget.sqlite3")


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


def test_us2_connection_reports_required_pragmas(tmp_path):
    from budget_app.db.connection import connect

    conn = connect(tmp_path / "db.sqlite3")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    conn.close()


def test_us2_connection_is_usable_from_another_thread(tmp_path):
    from budget_app.db.connection import connect

    conn = connect(tmp_path / "db.sqlite3")
    result = []
    errors = []

    def run():
        try:
            result.append(conn.execute("SELECT 41 + 1").fetchone()[0])
        except sqlite3.Error as exc:
            errors.append(exc)

    t = threading.Thread(target=run)
    t.start()
    t.join()
    assert errors == []
    assert result == [42]
    conn.close()


def test_us2_two_threads_writing_concurrently_all_commit(tmp_path):
    from budget_app.db.connection import connect

    path = tmp_path / "db.sqlite3"
    setup = connect(path)
    setup.execute("CREATE TABLE scratch (id INTEGER PRIMARY KEY, who INTEGER)")
    errors = []

    def writer(who):
        try:
            conn = connect(path)
            for _ in range(20):
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("INSERT INTO scratch (who) VALUES (?)", (who,))
                conn.execute("COMMIT")
            conn.close()
        except sqlite3.Error as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in (1, 2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert setup.execute("SELECT COUNT(*) FROM scratch").fetchone()[0] == 40
    assert setup.execute("SELECT COUNT(*) FROM scratch WHERE who=1").fetchone()[0] == 20
    setup.close()


def test_us2_budget_db_env_wins(tmp_path, monkeypatch, fake_home):
    from budget_app.db.connection import resolve_db_path

    target = tmp_path / "custom" / "mine.sqlite3"
    monkeypatch.setenv("BUDGET_DB", str(target))
    assert resolve_db_path() == target


def test_us2_empty_budget_db_falls_back_to_application_support(monkeypatch, fake_home):
    from budget_app.db.connection import resolve_db_path

    monkeypatch.setenv("BUDGET_DB", "")
    assert resolve_db_path() == fake_home / APP_SUPPORT


def test_us2_unset_budget_db_falls_back_to_application_support(monkeypatch, fake_home):
    from budget_app.db.connection import resolve_db_path

    monkeypatch.delenv("BUDGET_DB", raising=False)
    assert resolve_db_path() == fake_home / APP_SUPPORT


def test_us2_resolve_db_path_has_no_side_effects(monkeypatch, fake_home):
    from budget_app.db.connection import resolve_db_path

    monkeypatch.delenv("BUDGET_DB", raising=False)
    resolve_db_path()
    assert not (fake_home / "Library").exists()


def test_us2_default_db_path_creates_missing_folder(monkeypatch, fake_home):
    from budget_app.db.connection import default_db_path

    monkeypatch.delenv("BUDGET_DB", raising=False)
    path = default_db_path()
    assert path == fake_home / APP_SUPPORT
    assert path.parent.is_dir()


def test_us2_default_path_is_not_inside_repo(monkeypatch):
    from budget_app.db.connection import resolve_db_path

    monkeypatch.delenv("BUDGET_DB", raising=False)
    path = resolve_db_path().resolve()
    assert REPO_ROOT not in path.parents


def _git_status():
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout


def test_us2_writing_through_budget_db_leaves_git_status_unchanged(tmp_path, monkeypatch):
    from budget_app.db.connection import connect, resolve_db_path

    monkeypatch.setenv("BUDGET_DB", str(tmp_path / "work.sqlite3"))
    before = _git_status()
    conn = connect(resolve_db_path())
    conn.execute("CREATE TABLE t (x)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.close()
    assert (tmp_path / "work.sqlite3").exists()
    assert _git_status() == before
