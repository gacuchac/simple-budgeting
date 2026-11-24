"""Tests for password hashing and session tokens."""

import hashlib
import re
import sqlite3

from budget_app.db.connection import connect


def make_user(conn: sqlite3.Connection, email: str = "alice@example.test") -> int:
    return conn.execute("INSERT INTO users (email, pw_hash) VALUES (?, 'x')", (email,)).lastrowid


def test_us1_hash_password_is_argon2id_and_verifies_only_the_right_password():
    from budget_app.auth.passwords import hash_password, verify_password

    hashed = hash_password("abcdefg1!")

    assert hashed.startswith("$argon2id$")
    assert verify_password("abcdefg1!", hashed) is True
    assert verify_password("abcdefg2!", hashed) is False


def test_us2_start_stores_only_the_sha256_of_the_token(conn):
    from budget_app.auth import sessions

    token = sessions.start(conn, make_user(conn))

    rows = conn.execute("SELECT token_hash, created_at FROM sessions").fetchall()
    assert len(rows) == 1
    assert re.fullmatch(r"[0-9a-f]{64}", rows[0][0])
    assert rows[0][0] == hashlib.sha256(token.encode()).hexdigest()
    assert rows[0][0] != token
    assert rows[0][1]


def test_us2_each_session_gets_a_distinct_token(conn):
    from budget_app.auth import sessions

    user = make_user(conn)

    assert sessions.start(conn, user) != sessions.start(conn, user)


def test_us2_resolve_returns_the_user_or_none(conn):
    from budget_app.auth import sessions

    user = make_user(conn)
    token = sessions.start(conn, user)

    assert sessions.resolve(conn, token) == user
    assert sessions.resolve(conn, "nope") is None


def test_us2_end_revokes_the_session_and_ignores_unknown_tokens(conn):
    from budget_app.auth import sessions

    user = make_user(conn)
    token = sessions.start(conn, user)
    other = sessions.start(conn, user)

    sessions.end(conn, "unknown")
    sessions.end(conn, token)

    assert sessions.resolve(conn, token) is None
    assert sessions.resolve(conn, other) == user


def test_us2_deleting_the_user_ends_their_sessions(conn):
    from budget_app.auth import sessions

    user = make_user(conn)
    token = sessions.start(conn, user)

    conn.execute("DELETE FROM users WHERE id = ?", (user,))

    assert sessions.resolve(conn, token) is None


def test_us2_session_survives_reopening_the_database(tmp_path):
    from budget_app.auth import sessions

    from budget_app.db.migrate import migrate

    path = tmp_path / "r.db"
    first = connect(path)
    migrate(first)
    user = make_user(first)
    token = sessions.start(first, user)
    first.close()

    assert sessions.resolve(connect(path), token) == user
