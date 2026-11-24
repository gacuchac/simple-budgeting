"""SQL for the memberships table."""

import sqlite3

from budget_app.domain.access import BudgetAccess
from budget_app.repos.users import UserId


def add(conn: sqlite3.Connection, budget_id: int, user_id: UserId, role: str) -> None:
    """Make `user_id` a member of `budget_id` with `role`."""
    conn.execute(
        "INSERT INTO memberships (budget_id, user_id, role) VALUES (?, ?, ?)",
        (budget_id, user_id, role),
    )


def access_for(conn: sqlite3.Connection, budget_id: int, user_id: UserId) -> BudgetAccess | None:
    """Return the access `user_id` has to `budget_id`, or None when they are not a member."""
    row = conn.execute(
        "SELECT m.role, b.kind = 'personal' FROM memberships m JOIN budgets b ON b.id = m.budget_id"
        " WHERE m.budget_id = ? AND m.user_id = ?",
        (budget_id, user_id),
    ).fetchone()
    return None if row is None else BudgetAccess(budget_id, user_id, row[0], bool(row[1]))


def has_email(conn: sqlite3.Connection, access: BudgetAccess, email: str) -> bool:
    """Return whether a user with this email is a member of the budget."""
    row = conn.execute(
        "SELECT 1 FROM memberships m JOIN users u ON u.id = m.user_id WHERE m.budget_id = ? AND u.email = ?",
        (access.budget_id, email),
    ).fetchone()
    return row is not None
