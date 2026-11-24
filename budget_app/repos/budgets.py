"""SQL for the budgets table."""

import sqlite3
from dataclasses import dataclass
from typing import Literal

from budget_app.repos.users import UserId


@dataclass(frozen=True)
class BudgetSummary:
    """A budget as one member sees it."""

    id: int
    name: str
    kind: Literal["personal", "shared"]
    role: Literal["editor", "viewer"]


def insert(conn: sqlite3.Connection, name: str, kind: str, created_by: UserId) -> int:
    """Insert a budget and return its id."""
    cursor = conn.execute(
        "INSERT INTO budgets (name, kind, created_by) VALUES (?, ?, ?)",
        (name, kind, created_by),
    )
    return cursor.lastrowid


def for_user(conn: sqlite3.Connection, user_id: UserId) -> list[BudgetSummary]:
    """Return the budgets `user_id` is a member of, personal first, then by id."""
    rows = conn.execute(
        "SELECT b.id, b.name, b.kind, m.role FROM budgets b"
        " JOIN memberships m ON m.budget_id = b.id WHERE m.user_id = ?"
        " ORDER BY b.kind <> 'personal', b.id",
        (user_id,),
    )
    return [BudgetSummary(*row) for row in rows]
