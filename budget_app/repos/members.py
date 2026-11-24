"""SQL for the memberships table."""

import sqlite3

from budget_app.repos.users import UserId


def add(conn: sqlite3.Connection, budget_id: int, user_id: UserId, role: str) -> None:
    """Make `user_id` a member of `budget_id` with `role`."""
    conn.execute(
        "INSERT INTO memberships (budget_id, user_id, role) VALUES (?, ?, ?)",
        (budget_id, user_id, role),
    )
