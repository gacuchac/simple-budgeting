"""Opaque session tokens; only their SHA-256 hashes are stored."""

import hashlib
import secrets
import sqlite3
from datetime import UTC, datetime

from budget_app.repos import sessions as store
from budget_app.repos.users import UserId


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start(conn: sqlite3.Connection, user_id: UserId) -> str:
    """Create a session for `user_id`, store its token's hash and return the token."""
    token = secrets.token_urlsafe(32)
    store.insert(conn, _digest(token), user_id, datetime.now(UTC).isoformat())
    return token


def resolve(conn: sqlite3.Connection, token: str) -> UserId | None:
    """Return the user the session `token` belongs to, or None when it is unknown or ended."""
    return store.user_for(conn, _digest(token))


def end(conn: sqlite3.Connection, token: str) -> None:
    """Revoke the session `token`; an unknown token is ignored."""
    store.delete(conn, _digest(token))
