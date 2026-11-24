"""Tests for the migration runner, using synthetic migration files."""

import sqlite3
from pathlib import Path

import pytest

from budget_app.db.connection import connect

FIRST = "CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT);\n"
CHILD = "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id));\n"
SECOND = "ALTER TABLE parent ADD COLUMN note TEXT;\n" + CHILD


def write_migrations(directory: Path, files: dict[str, str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, sql in files.items():
        (directory / name).write_text(sql)
    return directory


def schema(conn: sqlite3.Connection) -> list[tuple]:
    return conn.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()


def user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def test_us3_applies_files_in_numeric_order_and_returns_final_version(tmp_path):
    from budget_app.db.migrate import migrate_from

    # 0002 depends on 0001; written in reverse so creation order cannot save a wrong sort.
    directory = write_migrations(tmp_path / "m", {"0002_second.sql": SECOND, "0001_first.sql": FIRST})
    conn = connect(tmp_path / "db.sqlite3")

    assert migrate_from(conn, directory) == 2
    assert user_version(conn) == 2
    tables = {row[1] for row in schema(conn) if row[0] == "table"}
    assert {"parent", "child"} <= tables


def test_us3_rerun_returns_same_version_and_leaves_schema_unchanged(tmp_path):
    from budget_app.db.migrate import migrate_from

    directory = write_migrations(tmp_path / "m", {"0001_first.sql": FIRST, "0002_second.sql": SECOND})
    conn = connect(tmp_path / "db.sqlite3")
    migrate_from(conn, directory)
    before = schema(conn)

    assert migrate_from(conn, directory) == 2
    assert schema(conn) == before


def test_us3_incremental_equals_fresh_and_keeps_rows(tmp_path):
    from budget_app.db.migrate import migrate_from

    both = write_migrations(tmp_path / "both", {"0001_first.sql": FIRST, "0002_second.sql": SECOND})
    only_first = write_migrations(tmp_path / "one", {"0001_first.sql": FIRST})

    fresh = connect(tmp_path / "fresh.sqlite3")
    assert migrate_from(fresh, both) == 2

    incremental = connect(tmp_path / "inc.sqlite3")
    assert migrate_from(incremental, only_first) == 1
    incremental.execute("INSERT INTO parent (id, name) VALUES (1, 'kept')")
    assert migrate_from(incremental, both) == 2

    assert schema(incremental) == schema(fresh)
    assert incremental.execute("SELECT id, name FROM parent").fetchall() == [(1, "kept")]


def test_us3_sql_error_raises_and_rolls_back_that_file(tmp_path):
    from budget_app.db.migrate import migrate_from

    bad = "CREATE TABLE half_done (id INTEGER);\nTHIS IS NOT SQL;\n"
    directory = write_migrations(tmp_path / "m", {"0001_first.sql": FIRST})
    conn = connect(tmp_path / "db.sqlite3")
    migrate_from(conn, directory)
    before = schema(conn)
    write_migrations(directory, {"0002_bad.sql": bad})

    with pytest.raises(sqlite3.Error):
        migrate_from(conn, directory)

    assert user_version(conn) == 1
    assert schema(conn) == before
    assert conn.in_transaction is False


def test_us3_foreign_key_violation_raises_and_rolls_back_that_file(tmp_path):
    from budget_app.db.migrate import migrate_from

    violating = "CREATE TABLE extra (id INTEGER);\nINSERT INTO child (id, parent_id) VALUES (1, 999);\n"
    directory = write_migrations(tmp_path / "m", {"0001_first.sql": FIRST + CHILD})
    conn = connect(tmp_path / "db.sqlite3")
    migrate_from(conn, directory)
    before = schema(conn)
    write_migrations(directory, {"0002_violating.sql": violating})

    with pytest.raises(sqlite3.IntegrityError):
        migrate_from(conn, directory)

    assert user_version(conn) == 1
    assert schema(conn) == before
    assert conn.execute("SELECT COUNT(*) FROM child").fetchone()[0] == 0
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_us3_foreign_keys_are_on_again_after_migrate_from(tmp_path):
    from budget_app.db.migrate import migrate_from

    directory = write_migrations(tmp_path / "m", {"0001_first.sql": FIRST, "0002_second.sql": SECOND})
    conn = connect(tmp_path / "db.sqlite3")

    migrate_from(conn, directory)

    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_us3_foreign_keys_are_off_while_a_file_runs(tmp_path):
    from budget_app.db.migrate import migrate_from

    # The child row is inserted before its parent exists; only valid with foreign keys off,
    # and the final state is consistent so the post-check passes.
    reorder = "INSERT INTO child (id, parent_id) VALUES (1, 7);\nINSERT INTO parent (id, name) VALUES (7, 'late');\n"
    directory = write_migrations(
        tmp_path / "m",
        {"0001_first.sql": FIRST + CHILD, "0002_reorder.sql": reorder},
    )
    conn = connect(tmp_path / "db.sqlite3")

    assert migrate_from(conn, directory) == 2
    assert conn.execute("SELECT parent_id FROM child").fetchall() == [(7,)]


def test_us3_ignores_files_not_matching_nnnn_pattern(tmp_path):
    from budget_app.db.migrate import migrate_from

    directory = write_migrations(
        tmp_path / "m",
        {
            "0001_first.sql": FIRST,
            "notes.txt": "CREATE TABLE from_txt (id INTEGER);",
            "abcd_words.sql": "CREATE TABLE from_alpha (id INTEGER);",
            "01_short.sql": "CREATE TABLE from_short (id INTEGER);",
            "0002_wrong_ext.sqlx": "CREATE TABLE from_ext (id INTEGER);",
            "9999.sql": "CREATE TABLE from_nounderscore (id INTEGER);",
        },
    )
    conn = connect(tmp_path / "db.sqlite3")

    assert migrate_from(conn, directory) == 1
    tables = {row[1] for row in schema(conn) if row[0] == "table"}
    assert tables == {"parent"}
