"""Tests for the accounts service: sign-up, sign-in and listing."""

import sqlite3

import pytest

GOOD = "abcdefg1!"
BAD_EMAILS = ["alice", "alice@", "@x.com", "a b@x.com", "alice@example"]
WEAK = ["abcdefgh", "abcdefg1", "ab1!"]
WEAK_PROBLEMS = {
    "abcdefgh": ["at least 1 number", "at least 1 special character"],
    "abcdefg1": ["at least 1 special character"],
    "ab1!": ["at least 8 characters"],
}


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def total_rows(conn):
    return {t: count(conn, t) for t in ("users", "budgets", "memberships", "categories")}


def test_us1_sign_up_creates_user_personal_budget_membership_and_categories(conn):
    from budget_app.services import accounts

    uid = accounts.sign_up(conn, " Alice@Example.Test ", GOOD)

    row = conn.execute("SELECT id, email, pw_hash FROM users").fetchall()
    assert len(row) == 1
    assert (row[0][0], row[0][1]) == (uid, "alice@example.test")
    assert row[0][2].startswith("$argon2id$")
    budget = conn.execute("SELECT id, name, kind, created_by FROM budgets").fetchall()
    assert [(b[1], b[2], b[3]) for b in budget] == [("Personal", "personal", uid)]
    assert conn.execute("SELECT budget_id, user_id, role FROM memberships").fetchall() == [(budget[0][0], uid, "editor")]
    kinds = conn.execute("SELECT kind, COUNT(*) FROM categories WHERE budget_id = ? GROUP BY kind", (budget[0][0],))
    assert dict(kinds.fetchall()) == {"expense": 7, "income": 3}
    summaries = accounts.budgets_for(conn, uid)
    assert [(s.id, s.name, s.kind, s.role) for s in summaries] == [(budget[0][0], "Personal", "personal", "editor")]


def test_us1_duplicate_email_in_any_case_raises_email_taken_and_writes_nothing(conn):
    from budget_app.services import accounts

    accounts.sign_up(conn, "alice@example.test", GOOD)
    before = total_rows(conn)

    with pytest.raises(accounts.EmailTaken):
        accounts.sign_up(conn, "ALICE@example.test ", GOOD)

    assert total_rows(conn) == before
    assert before["users"] == 1
    assert before["budgets"] == 1


@pytest.mark.parametrize("password", WEAK)
def test_us1_weak_password_raises_with_problems_and_writes_nothing(conn, password):
    from budget_app.services import accounts

    with pytest.raises(accounts.WeakPassword) as caught:
        accounts.sign_up(conn, "alice@example.test", password)

    assert caught.value.problems == WEAK_PROBLEMS[password]
    assert total_rows(conn) == dict.fromkeys(("users", "budgets", "memberships", "categories"), 0)


@pytest.mark.parametrize("email", BAD_EMAILS)
def test_us1_bad_email_raises_invalid_email_and_writes_nothing(conn, email):
    from budget_app.services import accounts

    with pytest.raises(accounts.InvalidEmail):
        accounts.sign_up(conn, email, GOOD)

    assert total_rows(conn) == dict.fromkeys(("users", "budgets", "memberships", "categories"), 0)


def test_us1_bad_email_is_reported_before_weak_password(conn):
    from budget_app.services import accounts

    with pytest.raises(accounts.InvalidEmail):
        accounts.sign_up(conn, "alice", "x")


def test_us1_failure_while_seeding_rolls_back_the_whole_sign_up(conn, monkeypatch):
    from budget_app.repos import categories
    from budget_app.services import accounts

    def boom(*args, **kwargs):
        raise sqlite3.OperationalError

    monkeypatch.setattr(categories, "seed_defaults", boom)

    with pytest.raises(sqlite3.OperationalError):
        accounts.sign_up(conn, "alice@example.test", GOOD)

    assert total_rows(conn) == dict.fromkeys(("users", "budgets", "memberships", "categories"), 0)


@pytest.mark.parametrize("email", ["alice@example.test", " ALICE@Example.Test "])
def test_us2_sign_in_with_right_password_returns_the_id(conn, email):
    from budget_app.services import accounts

    uid = accounts.sign_up(conn, "alice@example.test", GOOD)

    assert accounts.sign_in(conn, email, GOOD) == uid


@pytest.mark.parametrize(
    ("email", "password"),
    [("alice@example.test", "wrong-pw1!"), ("nobody@example.test", GOOD), ("alice", GOOD)],
)
def test_us2_sign_in_failures_return_none(conn, email, password):
    from budget_app.services import accounts

    accounts.sign_up(conn, "alice@example.test", GOOD)

    assert accounts.sign_in(conn, email, password) is None


def test_us2_account_returns_id_and_email(conn):
    from budget_app.services import accounts

    uid = accounts.sign_up(conn, "alice@example.test", GOOD)

    acct = accounts.account(conn, uid)
    assert (acct.id, acct.email) == (uid, "alice@example.test")


def test_us3_budgets_for_excludes_other_users_budgets(conn):
    from budget_app.services import accounts

    alice = accounts.sign_up(conn, "alice@example.test", GOOD)
    accounts.sign_up(conn, "bob@example.test", GOOD)

    assert len(accounts.budgets_for(conn, alice)) == 1
