"""Limits: set, list, delete, their status over a range, and the check for the expense form."""

import datetime as dt
import sqlite3
from collections.abc import Mapping

from budget_app.domain.access import BudgetAccess
from budget_app.domain.limits import Limit, LimitStatus, limit_status, period_containing
from budget_app.domain.periods import DateRange, PeriodUnit
from budget_app.domain.recurrence import occurrences
from budget_app.repos import categories, entries, limits


class LimitNotFound(LookupError):
    """The limit or its category is not in this budget."""


class InvalidLimit(ValueError):
    """The request breaks a rule; the message says which."""


def list_all(conn: sqlite3.Connection, access: BudgetAccess) -> list[Limit]:
    """Return the limits of the budget."""
    return limits.list_for(conn, access)


def set_limit(
    conn: sqlite3.Connection, access: BudgetAccess, category_id: int, amount_cents: int, period: PeriodUnit
) -> Limit:
    """Set the limit of an expense category, replacing its old one.

    Raises LimitNotFound when the category is not in the budget, InvalidLimit for an income category.
    """
    category = categories.get(conn, access, category_id)
    if category is None:
        raise LimitNotFound
    if category.kind != "expense":
        raise InvalidLimit("limits are for expense categories")
    return limits.upsert(conn, access, category_id, amount_cents, period)


def remove(conn: sqlite3.Connection, access: BudgetAccess, limit_id: int) -> None:
    """Delete a limit; raises LimitNotFound when it is not in the budget."""
    if not limits.delete(conn, access, limit_id):
        raise LimitNotFound


def statuses(
    conn: sqlite3.Connection, access: BudgetAccess, rng: DateRange, spent_by_category: Mapping[int | None, int]
) -> list[LimitStatus]:
    """Return the status of every limit of the budget over `rng`, given the cents spent per category in it."""
    return [limit_status(lim, rng, spent_by_category.get(lim.category_id, 0)) for lim in limits.list_for(conn, access)]


def _spent(
    conn: sqlite3.Connection, access: BudgetAccess, category_id: int, rng: DateRange, exclude_entry_id: int | None
) -> int:
    return sum(
        e.amount_cents
        for e in entries.list_for(conn, access)
        if e.kind == "expense" and e.category_id == category_id and e.id != exclude_entry_id
        for _ in occurrences(e.rule, rng.start, rng.end)
    )


def check(
    conn: sqlite3.Connection,
    access: BudgetAccess,
    category_id: int,
    day: dt.date,
    amount_cents: int,
    exclude_entry_id: int | None = None,
) -> LimitStatus | None:
    """Return the status of the category's limit over its own period containing `day`, counting `amount_cents` once more.

    The category's expenses in that period exclude every occurrence of `exclude_entry_id`.
    Returns None when the category has no limit; raises InvalidLimit for a category that is not an expense category
    of the budget, an unknown entry or a negative amount.
    """
    category = categories.get(conn, access, category_id)
    if category is None or category.kind != "expense":
        raise InvalidLimit("category_id is not an expense category of this budget")
    if exclude_entry_id is not None and entries.get(conn, access, exclude_entry_id) is None:
        raise InvalidLimit("exclude_entry_id is not an entry of this budget")
    if amount_cents < 0:
        raise InvalidLimit("amount_cents must not be negative")
    limit = limits.for_category(conn, access, category_id)
    if limit is None:
        return None
    rng = period_containing(limit.period, day)
    return limit_status(limit, rng, _spent(conn, access, category_id, rng, exclude_entry_id) + amount_cents)
