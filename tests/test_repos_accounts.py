"""Tests for the account repos: users, budgets, members and default categories."""

import dataclasses

import pytest

EXPENSE = {"Housing", "Food", "Transport", "Utilities", "Health", "Entertainment", "Other"}
INCOME = {"Salary", "Freelance", "Other"}


def names(conn, budget_id, kind):
    rows = conn.execute("SELECT name FROM categories WHERE budget_id = ? AND kind = ?", (budget_id, kind))
    return [r[0] for r in rows]


def test_us1_users_round_trip(conn):
    from budget_app.repos import users

    uid = users.insert(conn, "alice@example.test", "hash1")

    by_email = users.by_email(conn, "alice@example.test")
    assert by_email == users.by_id(conn, uid)
    assert (by_email.id, by_email.email, by_email.pw_hash) == (uid, "alice@example.test", "hash1")
    assert users.by_email(conn, "nobody@example.test") is None
    assert users.by_id(conn, uid + 100) is None


def test_us1_user_is_a_frozen_dataclass(conn):
    from budget_app.repos import users

    users.insert(conn, "alice@example.test", "h")
    user = users.by_email(conn, "alice@example.test")

    with pytest.raises(dataclasses.FrozenInstanceError):
        user.email = "other@example.test"


def test_us3_for_user_lists_own_memberships_with_role_and_hides_others(conn):
    from budget_app.repos import budgets, members, users

    alice = users.insert(conn, "alice@example.test", "h")
    bob = users.insert(conn, "bob@example.test", "h")
    shared = budgets.insert(conn, "Trip", "shared", bob)
    personal = budgets.insert(conn, "Personal", "personal", alice)
    members.add(conn, personal, alice, "editor")
    members.add(conn, shared, alice, "viewer")
    members.add(conn, shared, bob, "editor")
    bob_private = budgets.insert(conn, "Bob private", "personal", bob)
    members.add(conn, bob_private, bob, "editor")

    listed = budgets.for_user(conn, alice)

    assert [(b.id, b.name, b.kind, b.role) for b in listed] == [
        (personal, "Personal", "personal", "editor"),
        (shared, "Trip", "shared", "viewer"),
    ]
    assert [b.name for b in budgets.for_user(conn, bob)] == ["Bob private", "Trip"]


def test_us3_for_user_puts_personal_first_then_orders_by_id(conn):
    from budget_app.repos import budgets, members, users

    alice = users.insert(conn, "alice@example.test", "h")
    first_shared = budgets.insert(conn, "A shared", "shared", alice)
    personal = budgets.insert(conn, "Personal", "personal", alice)
    second_shared = budgets.insert(conn, "B shared", "shared", alice)
    for bid in (first_shared, personal, second_shared):
        members.add(conn, bid, alice, "editor")

    assert [b.id for b in budgets.for_user(conn, alice)] == [personal, first_shared, second_shared]


def test_us1_seed_defaults_gives_each_budget_its_own_ten_categories(conn):
    from budget_app.domain.access import BudgetAccess
    from budget_app.repos import budgets, categories, users

    alice = users.insert(conn, "alice@example.test", "h")
    one = budgets.insert(conn, "Personal", "personal", alice)
    two = budgets.insert(conn, "Other", "shared", alice)

    categories.seed_defaults(conn, BudgetAccess(one, alice, "editor", True))
    categories.seed_defaults(conn, BudgetAccess(two, alice, "editor", False))

    for bid in (one, two):
        assert sorted(names(conn, bid, "expense")) == sorted(EXPENSE)
        assert sorted(names(conn, bid, "income")) == sorted(INCOME)
    assert conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 20


def test_us1_default_category_constants(conn):
    from budget_app.repos import categories

    assert set(categories.DEFAULT_EXPENSE) == EXPENSE
    assert len(categories.DEFAULT_EXPENSE) == 7
    assert set(categories.DEFAULT_INCOME) == INCOME
    assert len(categories.DEFAULT_INCOME) == 3


def test_us1_budget_access_is_frozen_with_contract_fields():
    from budget_app.domain.access import BudgetAccess

    access = BudgetAccess(budget_id=1, user_id=2, role="viewer", is_personal=False)

    assert [f.name for f in dataclasses.fields(BudgetAccess)] == ["budget_id", "user_id", "role", "is_personal"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        access.role = "editor"
