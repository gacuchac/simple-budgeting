"""SQL for the limits table."""

import sqlite3

from budget_app.domain.access import BudgetAccess
from budget_app.domain.limits import Limit
from budget_app.domain.periods import PeriodUnit

_COLUMNS = "id, budget_id, category_id, amount_cents, period"


def list_for(conn: sqlite3.Connection, access: BudgetAccess) -> list[Limit]:
    """Return the limits of the budget, by id."""
    rows = conn.execute(f"SELECT {_COLUMNS} FROM limits WHERE budget_id = ? ORDER BY id", (access.budget_id,))
    return [Limit(*row) for row in rows]


def for_category(conn: sqlite3.Connection, access: BudgetAccess, category_id: int) -> Limit | None:
    """Return the limit of the category in the budget, or None when it has none."""
    row = conn.execute(
        f"SELECT {_COLUMNS} FROM limits WHERE budget_id = ? AND category_id = ?", (access.budget_id, category_id)
    ).fetchone()
    return None if row is None else Limit(*row)


def upsert(
    conn: sqlite3.Connection, access: BudgetAccess, category_id: int, amount_cents: int, period: PeriodUnit
) -> Limit:
    """Set the category's limit, replacing any old one, and return it."""
    conn.execute(
        "INSERT INTO limits (budget_id, category_id, amount_cents, period) VALUES (?, ?, ?, ?)"
        " ON CONFLICT (category_id) DO UPDATE SET amount_cents = excluded.amount_cents, period = excluded.period",
        (access.budget_id, category_id, amount_cents, period),
    )
    return for_category(conn, access, category_id)


def delete(conn: sqlite3.Connection, access: BudgetAccess, limit_id: int) -> bool:
    """Delete a limit of the budget; False when it is not there."""
    cursor = conn.execute("DELETE FROM limits WHERE id = ? AND budget_id = ?", (limit_id, access.budget_id))
    return cursor.rowcount == 1
