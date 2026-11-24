"""Accounts: sign-up, sign-in and the caller's budgets."""

import sqlite3
from dataclasses import dataclass

from budget_app.auth.passwords import hash_password, verify_password
from budget_app.domain.access import BudgetAccess
from budget_app.domain.accounts import normalise_email, password_problems
from budget_app.repos import budgets, categories, members, users
from budget_app.repos.budgets import BudgetSummary
from budget_app.repos.users import UserId


class InvalidEmail(ValueError):
    """The email is not an address."""


class WeakPassword(ValueError):
    """The password breaks rules; `problems` names them."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__()
        self.problems = problems


class EmailTaken(Exception):
    """An account with this email already exists."""


@dataclass(frozen=True)
class Account:
    """The public face of a user."""

    id: UserId
    email: str


def _create(conn: sqlite3.Connection, email: str, pw_hash: str) -> UserId:
    if users.by_email(conn, email):
        raise EmailTaken
    user_id = users.insert(conn, email, pw_hash)
    budget_id = budgets.insert(conn, "Personal", "personal", user_id)
    members.add(conn, budget_id, user_id, "editor")
    categories.seed_defaults(conn, BudgetAccess(budget_id, user_id, "editor", True))
    return user_id


def sign_up(conn: sqlite3.Connection, raw_email: str, password: str) -> UserId:
    """Create a user with a personal budget and default categories in one transaction.

    Raises InvalidEmail, then WeakPassword, before writing; EmailTaken when the email exists.
    """
    email = normalise_email(raw_email)
    if email is None:
        raise InvalidEmail
    problems = password_problems(password)
    if problems:
        raise WeakPassword(problems)
    pw_hash = hash_password(password)
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        return _create(conn, email, pw_hash)


def sign_in(conn: sqlite3.Connection, raw_email: str, password: str) -> UserId | None:
    """Return the user id when the email and password match, else None."""
    email = normalise_email(raw_email)
    user = users.by_email(conn, email) if email else None
    if user is None or not verify_password(password, user.pw_hash):
        return None
    return user.id


def account(conn: sqlite3.Connection, user_id: UserId) -> Account:
    """Return the id and email of the existing user `user_id`."""
    user = users.by_id(conn, user_id)
    return Account(user.id, user.email)


def budgets_for(conn: sqlite3.Connection, user_id: UserId) -> list[BudgetSummary]:
    """Return the budgets `user_id` belongs to, personal first."""
    return budgets.for_user(conn, user_id)
