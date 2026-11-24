"""Step 3 CI spike: the Python runtime pieces the plan relies on also work on the CI runner."""

import sqlite3
import sys


def test_password_hash_round_trip() -> None:
    """pwdlib's recommended hasher gives argon2id hashes that verify only the right password."""
    from pwdlib import PasswordHash

    hasher = PasswordHash.recommended()
    stored = hasher.hash("abcdefg1!")
    assert stored.startswith("$argon2id$")
    assert hasher.verify("abcdefg1!", stored)
    assert not hasher.verify("abcdefg2!", stored)


def test_sqlite_foreign_keys_and_wal(tmp_path: object) -> None:
    """The runner's SQLite enforces ON DELETE SET NULL once foreign_keys is on, and accepts WAL."""
    conn = sqlite3.connect(f"{tmp_path}/ci.sqlite3")
    conn.execute("PRAGMA foreign_keys=ON")
    mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    conn.execute("CREATE TABLE c(id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE e(id INTEGER PRIMARY KEY, c INTEGER REFERENCES c(id) ON DELETE SET NULL)")
    conn.execute("INSERT INTO c VALUES(1)")
    conn.execute("INSERT INTO e VALUES(1, 1)")
    conn.execute("DELETE FROM c WHERE id=1")
    print(f"python {sys.version.split()[0]} sqlite {sqlite3.sqlite_version}")
    assert mode == "wal"
    assert conn.execute("SELECT c FROM e").fetchone()[0] is None
