"""Forward-only SQL migration runner driven by `PRAGMA user_version`."""

import re
import sqlite3
from collections.abc import Iterator
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_MIGRATION_NAME = re.compile(r"(\d{4})_.*\.sql")


def _pending(directory: Path, current: int) -> list[tuple[int, Path]]:
    found = [(int(m[1]), path) for path in directory.iterdir() if (m := _MIGRATION_NAME.fullmatch(path.name))]
    return sorted((n, path) for n, path in found if n > current)


def _statements(sql: str) -> Iterator[str]:
    buffer = ""
    for piece in sql.split(";"):
        buffer += piece + ";"
        if sqlite3.complete_statement(buffer):
            yield buffer
            buffer = ""
    if buffer.strip(";").strip():
        yield buffer.strip(";")


def _apply(conn: sqlite3.Connection, number: int, sql: str) -> None:
    conn.execute("BEGIN")
    try:
        for statement in _statements(sql):
            conn.execute(statement)
        conn.execute(f"PRAGMA user_version={number}")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError(f"migration {number:04d} violates foreign keys: {violations}")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


def migrate_from(conn: sqlite3.Connection, directory: Path) -> int:
    """Apply every `NNNN_*.sql` file in `directory` numbered above `user_version`, in numeric order.

    Each file runs in one transaction that also sets `user_version` to its number, with foreign
    keys off during the file and on again afterwards, also after a failure. A non-empty
    `PRAGMA foreign_key_check` rolls that file back and raises `sqlite3.IntegrityError`; a SQL
    error rolls it back and propagates. Returns the final `user_version`.
    """
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, path in _pending(directory, current):
        conn.execute("PRAGMA foreign_keys=OFF")
        try:
            _apply(conn, number, path.read_text())
        finally:
            conn.execute("PRAGMA foreign_keys=ON")
        current = number
    return current


def migrate(conn: sqlite3.Connection) -> int:
    """Apply the packaged migrations to `conn` and return the final `user_version`."""
    return migrate_from(conn, MIGRATIONS_DIR)
