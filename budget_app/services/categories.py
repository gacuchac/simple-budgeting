"""Categories of a budget: list, add, rename, delete."""

import sqlite3

from budget_app.domain.access import BudgetAccess
from budget_app.repos import categories
from budget_app.repos.categories import Category, Kind


class NameTaken(Exception):
    """The budget already has a category of this kind with this name."""


class CategoryNotFound(LookupError):
    """The category is not in this budget."""


def list_all(conn: sqlite3.Connection, access: BudgetAccess) -> list[Category]:
    """Return the categories of the budget."""
    return categories.list_for(conn, access)


def add(conn: sqlite3.Connection, access: BudgetAccess, kind: Kind, name: str) -> Category:
    """Add a category and return it; raises NameTaken when the name exists for the kind."""
    try:
        return categories.insert(conn, access, kind, name)
    except sqlite3.IntegrityError:
        raise NameTaken from None


def rename(conn: sqlite3.Connection, access: BudgetAccess, category_id: int, name: str) -> Category:
    """Rename a category and return it; raises NameTaken on a duplicate, CategoryNotFound when not in the budget."""
    try:
        found = categories.rename(conn, access, category_id, name)
    except sqlite3.IntegrityError:
        raise NameTaken from None
    category = categories.get(conn, access, category_id) if found else None
    if category is None:
        raise CategoryNotFound
    return category


def remove(conn: sqlite3.Connection, access: BudgetAccess, category_id: int) -> None:
    """Delete a category (its entries become uncategorized); raises CategoryNotFound when it is not in the budget."""
    if not categories.delete(conn, access, category_id):
        raise CategoryNotFound
