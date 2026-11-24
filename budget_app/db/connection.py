"""SQLite connection factory and default database path."""

import os
import sqlite3
from pathlib import Path

_APP_SUPPORT_DB = "Library/Application Support/budget-app/budget.sqlite3"


def connect(path: Path) -> sqlite3.Connection:
    """Open a SQLite connection to `path` with autocommit, foreign keys, WAL and a 5s busy timeout.

    The connection may be used from any thread.
    """
    conn = sqlite3.connect(path, timeout=5, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def resolve_db_path() -> Path:
    """Return the database path: BUDGET_DB if set and non-empty, else the Application Support default.

    Has no side effects.
    """
    override = os.environ.get("BUDGET_DB")
    return Path(override) if override else Path.home() / _APP_SUPPORT_DB


def default_db_path() -> Path:
    """Return `resolve_db_path()` after creating its parent folder."""
    path = resolve_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
