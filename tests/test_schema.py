"""Schema tests for the core tables created by the packaged migrations."""

import re
import sqlite3
from pathlib import Path

import pytest

from budget_app.db.connection import connect
from budget_app.db.migrate import migrate

# Table-driven: later migrations extend this dict with their tables.
# "fks": (column, referenced table) -> on_delete; "checks": fragments that must appear in the table SQL.
EXPECTED = {
    "users": {"fks": {}, "checks": []},
    "sessions": {"fks": {("user_id", "users"): "CASCADE"}, "checks": []},
    "budgets": {
        "fks": {("created_by", "users"): "CASCADE"},
        "checks": ["kind IN ('personal','shared')"],
    },
    "memberships": {
        "fks": {("budget_id", "budgets"): "CASCADE", ("user_id", "users"): "CASCADE"},
        "checks": ["role IN ('editor','viewer')"],
    },
    "categories": {
        "fks": {("budget_id", "budgets"): "CASCADE"},
        "checks": ["kind IN ('income','expense')"],
    },
    "entries": {
        "fks": {("budget_id", "budgets"): "CASCADE", ("category_id", "categories"): "SET NULL"},
        "checks": [
            "kind IN ('income','expense')",
            "amount_cents > 0",
            "rule_type IN ('one_off','every','monthly_on_day')",
            "every_unit IN ('day','week','month')",
            "every_n >= 1",
            "month_day BETWEEN 1 AND 31",
            "source IS NULL OR kind = 'income'",
            "end_date IS NULL OR end_date >= start_date",
        ],
    },
}

ONE_OFF = {"rule_type": "one_off", "start_date": "2026-03-10"}
EVERY = {"rule_type": "every", "start_date": "2026-03-10", "every_n": 2, "every_unit": "week"}
MONTHLY = {"rule_type": "monthly_on_day", "start_date": "2026-03-10", "month_day": 5}

# (table, overrides on a valid row) pairs that each break exactly one CHECK.
BAD_ROWS = {
    "budgets_kind": ("budgets", {"kind": "public"}),
    "memberships_role": ("memberships", {"role": "owner"}),
    "categories_kind": ("categories", {"kind": "savings"}),
    "entries_kind": ("entries", {**ONE_OFF, "kind": "transfer"}),
    "entries_amount_zero": ("entries", {**ONE_OFF, "amount_cents": 0}),
    "entries_amount_negative": ("entries", {**ONE_OFF, "amount_cents": -500}),
    "entries_source_on_expense": ("entries", {**ONE_OFF, "kind": "expense", "source": "Acme"}),
    "entries_rule_type": ("entries", {**ONE_OFF, "rule_type": "weekly"}),
    "entries_end_before_start": ("entries", {**EVERY, "end_date": "2026-03-09"}),
    "entries_every_n_zero": ("entries", {**EVERY, "every_n": 0}),
    "entries_every_unit": ("entries", {**EVERY, "every_unit": "year"}),
    "entries_month_day_zero": ("entries", {**MONTHLY, "month_day": 0}),
    "entries_month_day_32": ("entries", {**MONTHLY, "month_day": 32}),
    "entries_one_off_with_end_date": ("entries", {**ONE_OFF, "end_date": "2026-04-01"}),
    "entries_one_off_with_every": ("entries", {**ONE_OFF, "every_n": 1, "every_unit": "day"}),
    "entries_one_off_with_month_day": ("entries", {**ONE_OFF, "month_day": 5}),
    "entries_every_without_every": ("entries", {"rule_type": "every", "start_date": "2026-03-10"}),
    "entries_every_without_unit": ("entries", {**EVERY, "every_unit": None}),
    "entries_every_with_month_day": ("entries", {**EVERY, "month_day": 5}),
    "entries_monthly_without_month_day": ("entries", {**MONTHLY, "month_day": None}),
    "entries_monthly_with_every": ("entries", {**MONTHLY, "every_n": 1, "every_unit": "month"}),
}


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    connection = connect(tmp_path / "budget.sqlite3")
    migrate(connection)
    return connection


def normalise(sql: str) -> str:
    return re.sub(r"\s+", "", sql).lower()


def schema(conn: sqlite3.Connection) -> list[tuple]:
    return conn.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()


def insert(conn: sqlite3.Connection, table: str, **values: object) -> int:
    columns = ", ".join(values)
    marks = ", ".join("?" for _ in values)
    cursor = conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({marks})", list(values.values()))
    return cursor.lastrowid


def make_user(conn: sqlite3.Connection, email: str = "a@example.test") -> int:
    return insert(conn, "users", email=email, pw_hash="$argon2id$x")


def make_budget(conn: sqlite3.Connection, user_id: int, kind: str = "personal") -> int:
    return insert(conn, "budgets", name="Home", kind=kind, created_by=user_id)


def make_category(conn: sqlite3.Connection, budget_id: int, name: str = "Food", kind: str = "expense") -> int:
    return insert(conn, "categories", budget_id=budget_id, kind=kind, name=name)


def make_entry(conn: sqlite3.Connection, budget_id: int, **overrides: object) -> int:
    row = {"budget_id": budget_id, "kind": "expense", "name": "Rent", "amount_cents": 1000, **ONE_OFF}
    row.update(overrides)
    return insert(conn, "entries", **row)


def count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_us4_migrate_creates_schema_at_version_1_and_rerun_changes_nothing(tmp_path):
    conn = connect(tmp_path / "budget.sqlite3")
    assert migrate(conn) == 1
    before = schema(conn)
    assert migrate(conn) == 1
    assert schema(conn) == before
    tables = {row[1] for row in before if row[0] == "table"}
    assert set(EXPECTED) <= tables


@pytest.mark.parametrize("table", sorted(t for t in EXPECTED if EXPECTED[t]["fks"]))
def test_us4_foreign_keys_have_expected_on_delete(conn, table):
    rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    actual = {(row[3], row[2]): row[6] for row in rows}
    assert actual == EXPECTED[table]["fks"]


@pytest.mark.parametrize("table", sorted(EXPECTED))
def test_us4_checks_appear_in_table_sql(conn, table):
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    assert sql is not None, f"table {table} is missing"
    for fragment in EXPECTED[table]["checks"]:
        assert normalise(fragment) in normalise(sql[0])


@pytest.mark.parametrize("case", sorted(BAD_ROWS))
def test_us4_row_breaking_a_check_is_rejected(conn, case):
    table, overrides = BAD_ROWS[case]
    user = make_user(conn)
    budget = make_budget(conn, user)
    parents = {
        "budgets": {"name": "Home", "kind": "personal", "created_by": user},
        "memberships": {"budget_id": budget, "user_id": user, "role": "editor"},
        "categories": {"budget_id": budget, "kind": "expense", "name": "Food"},
        "entries": {"budget_id": budget, "kind": "expense", "name": "Rent", "amount_cents": 1000},
    }
    row = {**parents[table], **overrides}
    if table == "memberships":
        conn.execute("DELETE FROM memberships")
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, table, **row)


def test_us4_valid_rule_shapes_and_income_source_are_accepted(conn):
    budget = make_budget(conn, make_user(conn))
    make_entry(conn, budget, **EVERY, end_date="2026-03-10")
    make_entry(conn, budget, **MONTHLY, end_date="2027-01-01")
    make_entry(conn, budget, **{**MONTHLY, "month_day": 31})
    make_entry(conn, budget, kind="income", source="Acme", **ONE_OFF)
    assert count(conn, "entries") == 4


def test_us4_email_must_be_unique(conn):
    make_user(conn, "dup@example.test")
    with pytest.raises(sqlite3.IntegrityError):
        make_user(conn, "dup@example.test")


def test_us4_category_name_is_unique_per_budget_and_kind(conn):
    budget = make_budget(conn, make_user(conn))
    make_category(conn, budget, "Food", "expense")
    make_category(conn, budget, "Food", "income")
    with pytest.raises(sqlite3.IntegrityError):
        make_category(conn, budget, "Food", "expense")


def test_us4_membership_pair_is_unique(conn):
    user = make_user(conn)
    budget = make_budget(conn, user)
    insert(conn, "memberships", budget_id=budget, user_id=user, role="editor")
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, "memberships", budget_id=budget, user_id=user, role="viewer")


def test_us4_deleting_a_category_sets_its_entries_category_to_null(conn):
    budget = make_budget(conn, make_user(conn))
    category = make_category(conn, budget)
    other = make_category(conn, budget, "Other")
    gone = make_entry(conn, budget, category_id=category)
    kept = make_entry(conn, budget, category_id=other)
    conn.execute("DELETE FROM categories WHERE id=?", (category,))
    rows = dict(conn.execute("SELECT id, category_id FROM entries").fetchall())
    assert rows == {gone: None, kept: other}


def test_us4_deleting_a_budget_leaves_no_orphans(conn):
    owner = make_user(conn)
    member = make_user(conn, "b@example.test")
    budget = make_budget(conn, owner, "shared")
    survivor = make_budget(conn, owner)
    insert(conn, "memberships", budget_id=budget, user_id=owner, role="editor")
    insert(conn, "memberships", budget_id=budget, user_id=member, role="viewer")
    category = make_category(conn, budget)
    make_entry(conn, budget, category_id=category)
    make_entry(conn, budget)
    keep_category = make_category(conn, survivor)
    make_entry(conn, survivor, category_id=keep_category)
    conn.execute("DELETE FROM budgets WHERE id=?", (budget,))
    for table in ("memberships", "categories", "entries"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE budget_id=?", (budget,)).fetchone()[0] == 0
    assert count(conn, "categories") == 1
    assert count(conn, "entries") == 1
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_us4_deleting_a_user_removes_their_sessions(conn):
    gone = make_user(conn)
    kept = make_user(conn, "b@example.test")
    insert(conn, "sessions", token_hash="a" * 64, user_id=gone, created_at="2026-03-10T00:00:00Z")
    insert(conn, "sessions", token_hash="b" * 64, user_id=gone, created_at="2026-03-10T00:00:00Z")
    insert(conn, "sessions", token_hash="c" * 64, user_id=kept, created_at="2026-03-10T00:00:00Z")
    conn.execute("DELETE FROM users WHERE id=?", (gone,))
    assert conn.execute("SELECT token_hash FROM sessions").fetchall() == [("c" * 64,)]


def test_us4_session_requires_created_at_and_a_real_user(conn):
    user = make_user(conn)
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, "sessions", token_hash="d" * 64, user_id=user, created_at=None)
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, "sessions", token_hash="e" * 64, user_id=9999, created_at="2026-03-10T00:00:00Z")
