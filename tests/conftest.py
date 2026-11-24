"""Shared fixtures."""

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    """A migrated connection to a fresh temporary database."""
    from budget_app.db.connection import connect
    from budget_app.db.migrate import migrate

    connection = connect(tmp_path / "t.db")
    migrate(connection)
    return connection
