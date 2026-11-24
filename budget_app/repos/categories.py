"""SQL for the categories table."""

import sqlite3
from dataclasses import dataclass
from typing import Literal

from budget_app.domain.access import BudgetAccess

DEFAULT_EXPENSE = ("Housing", "Food", "Transport", "Utilities", "Health", "Entertainment", "Other")
DEFAULT_INCOME = ("Salary", "Freelance", "Other")

Kind = Literal["income", "expense"]


@dataclass(frozen=True)
class Category:
    """One category of a budget."""

    id: int
    budget_id: int
    kind: Kind
    name: str


def seed_defaults(conn: sqlite3.Connection, access: BudgetAccess) -> None:
    """Insert the default expense and income categories into the budget `access.budget_id`."""
    rows = [(access.budget_id, "expense", name) for name in DEFAULT_EXPENSE]
    rows += [(access.budget_id, "income", name) for name in DEFAULT_INCOME]
    conn.executemany("INSERT INTO categories (budget_id, kind, name) VALUES (?, ?, ?)", rows)


def list_for(conn: sqlite3.Connection, access: BudgetAccess) -> list[Category]:
    """Return the categories of the budget `access.budget_id`, income first, then by id."""
    rows = conn.execute(
        "SELECT id, budget_id, kind, name FROM categories WHERE budget_id = ? ORDER BY kind <> 'income', id",
        (access.budget_id,),
    )
    return [Category(*row) for row in rows]


def get(conn: sqlite3.Connection, access: BudgetAccess, category_id: int) -> Category | None:
    """Return the category `category_id` of the budget, or None when it is not in this budget."""
    row = conn.execute(
        "SELECT id, budget_id, kind, name FROM categories WHERE id = ? AND budget_id = ?",
        (category_id, access.budget_id),
    ).fetchone()
    return None if row is None else Category(*row)


def insert(conn: sqlite3.Connection, access: BudgetAccess, kind: Kind, name: str) -> Category:
    """Insert a category into the budget and return it; sqlite3.IntegrityError when the name exists for the kind."""
    cursor = conn.execute(
        "INSERT INTO categories (budget_id, kind, name) VALUES (?, ?, ?)", (access.budget_id, kind, name)
    )
    return Category(cursor.lastrowid, access.budget_id, kind, name)


def rename(conn: sqlite3.Connection, access: BudgetAccess, category_id: int, name: str) -> bool:
    """Rename a category of the budget; False when it is not there, sqlite3.IntegrityError on a duplicate name."""
    cursor = conn.execute(
        "UPDATE categories SET name = ? WHERE id = ? AND budget_id = ?", (name, category_id, access.budget_id)
    )
    return cursor.rowcount == 1


def delete(conn: sqlite3.Connection, access: BudgetAccess, category_id: int) -> bool:
    """Delete a category of the budget; False when it is not there. Its entries become uncategorized."""
    cursor = conn.execute("DELETE FROM categories WHERE id = ? AND budget_id = ?", (category_id, access.budget_id))
    return cursor.rowcount == 1
