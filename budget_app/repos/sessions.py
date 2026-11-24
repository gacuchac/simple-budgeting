"""SQL for the sessions table."""

import sqlite3

from budget_app.repos.users import UserId


def insert(conn: sqlite3.Connection, token_hash: str, user_id: UserId, created_at: str) -> None:
    """Store a session row for `user_id`."""
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at) VALUES (?, ?, ?)",
        (token_hash, user_id, created_at),
    )


def user_for(conn: sqlite3.Connection, token_hash: str) -> UserId | None:
    """Return the user owning the session `token_hash`, or None."""
    row = conn.execute("SELECT user_id FROM sessions WHERE token_hash = ?", (token_hash,)).fetchone()
    return UserId(row[0]) if row else None


def delete(conn: sqlite3.Connection, token_hash: str) -> None:
    """Delete the session `token_hash`; an unknown hash is ignored."""
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
