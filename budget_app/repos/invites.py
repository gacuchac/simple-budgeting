"""SQL for the invites table."""

import sqlite3
from dataclasses import dataclass

from budget_app.domain.access import BudgetAccess

_SELECT = (
    "SELECT i.id, i.budget_id, b.name, i.email, i.invited_by, u.email, i.status FROM invites i"
    " JOIN budgets b ON b.id = i.budget_id JOIN users u ON u.id = i.invited_by"
)


@dataclass(frozen=True)
class Invite:
    """An invite with its budget name and the email of who sent it."""

    id: int
    budget_id: int
    budget_name: str
    email: str
    invited_by: int
    invited_by_email: str
    status: str


def insert(conn: sqlite3.Connection, access: BudgetAccess, email: str) -> int:
    """Insert a pending invite of `email` to the budget, sent by the caller, and return its id."""
    cursor = conn.execute(
        "INSERT INTO invites (budget_id, email, invited_by) VALUES (?, ?, ?)",
        (access.budget_id, email, access.user_id),
    )
    return cursor.lastrowid


def get(conn: sqlite3.Connection, invite_id: int) -> Invite | None:
    """Return the invite with this id, or None."""
    row = conn.execute(f"{_SELECT} WHERE i.id = ?", (invite_id,)).fetchone()
    return Invite(*row) if row else None


def pending_in_budget(conn: sqlite3.Connection, access: BudgetAccess) -> list[Invite]:
    """Return the budget's pending invites, oldest first."""
    rows = conn.execute(f"{_SELECT} WHERE i.budget_id = ? AND i.status = 'pending' ORDER BY i.id", (access.budget_id,))
    return [Invite(*row) for row in rows]


def pending_for_email(conn: sqlite3.Connection, email: str) -> list[Invite]:
    """Return the pending invites addressed to the normalised `email`, oldest first."""
    rows = conn.execute(f"{_SELECT} WHERE i.email = ? AND i.status = 'pending' ORDER BY i.id", (email,))
    return [Invite(*row) for row in rows]


def has_pending(conn: sqlite3.Connection, access: BudgetAccess, email: str) -> bool:
    """Return whether the budget already has a pending invite for `email`."""
    row = conn.execute(
        "SELECT 1 FROM invites WHERE budget_id = ? AND email = ? AND status = 'pending'",
        (access.budget_id, email),
    ).fetchone()
    return row is not None


def set_status(conn: sqlite3.Connection, invite_id: int, status: str) -> None:
    """Set the status of the invite."""
    conn.execute("UPDATE invites SET status = ? WHERE id = ?", (status, invite_id))


def delete(conn: sqlite3.Connection, invite_id: int) -> None:
    """Delete the invite."""
    conn.execute("DELETE FROM invites WHERE id = ?", (invite_id,))
