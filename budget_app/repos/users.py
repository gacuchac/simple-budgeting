"""SQL for the users table."""

import sqlite3
from dataclasses import dataclass
from typing import NewType

UserId = NewType("UserId", int)


@dataclass(frozen=True)
class User:
    """A stored user."""

    id: UserId
    email: str
    pw_hash: str


def _user(row: tuple | None) -> User | None:
    return User(UserId(row[0]), row[1], row[2]) if row else None


def insert(conn: sqlite3.Connection, email: str, pw_hash: str) -> UserId:
    """Insert a user and return its id; a duplicate email raises sqlite3.IntegrityError."""
    cursor = conn.execute("INSERT INTO users (email, pw_hash) VALUES (?, ?)", (email, pw_hash))
    return UserId(cursor.lastrowid)


def by_email(conn: sqlite3.Connection, email: str) -> User | None:
    """Return the user with exactly this email, or None."""
    row = conn.execute("SELECT id, email, pw_hash FROM users WHERE email = ?", (email,)).fetchone()
    return _user(row)


def by_id(conn: sqlite3.Connection, user_id: UserId) -> User | None:
    """Return the user with this id, or None."""
    row = conn.execute("SELECT id, email, pw_hash FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user(row)
