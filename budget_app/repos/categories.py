"""SQL for the categories table."""

import sqlite3

from budget_app.domain.access import BudgetAccess

DEFAULT_EXPENSE = ("Housing", "Food", "Transport", "Utilities", "Health", "Entertainment", "Other")
DEFAULT_INCOME = ("Salary", "Freelance", "Other")


def seed_defaults(conn: sqlite3.Connection, access: BudgetAccess) -> None:
    """Insert the default expense and income categories into the budget `access.budget_id`."""
    rows = [(access.budget_id, "expense", name) for name in DEFAULT_EXPENSE]
    rows += [(access.budget_id, "income", name) for name in DEFAULT_INCOME]
    conn.executemany("INSERT INTO categories (budget_id, kind, name) VALUES (?, ?, ?)", rows)
