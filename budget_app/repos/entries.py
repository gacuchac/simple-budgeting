"""SQL for the entries table."""

import datetime as dt
import sqlite3
from dataclasses import dataclass
from typing import Literal

from budget_app.domain.access import BudgetAccess
from budget_app.domain.recurrence import Every, MonthlyOnDay, OneOff, Rule

Kind = Literal["income", "expense"]

_COLUMNS = (
    "id, budget_id, kind, name, amount_cents, category_id, source,"
    " rule_type, start_date, end_date, every_n, every_unit, month_day"
)


@dataclass(frozen=True)
class Draft:
    """The editable fields of an entry."""

    kind: Kind
    name: str
    amount_cents: int
    category_id: int | None
    source: str | None
    rule: Rule


@dataclass(frozen=True)
class Entry(Draft):
    """A stored entry."""

    id: int
    budget_id: int


def _iso(d: dt.date | None) -> str | None:
    return None if d is None else d.isoformat()


def _date(text: str | None) -> dt.date | None:
    return None if text is None else dt.date.fromisoformat(text)


def _rule_columns(rule: Rule) -> tuple:
    """Return (rule_type, start_date, end_date, every_n, every_unit, month_day) for `rule`."""
    match rule:
        case OneOff(date=d):
            return ("one_off", _iso(d), None, None, None, None)
        case Every():
            return ("every", _iso(rule.start), _iso(rule.end), rule.n, rule.unit, None)
        case MonthlyOnDay():
            return ("monthly_on_day", _iso(rule.start), _iso(rule.end), None, None, rule.day)


def _rule(rule_type: str, start: str, end: str | None, n: int | None, unit: str | None, day: int | None) -> Rule:
    first, last = dt.date.fromisoformat(start), _date(end)
    if rule_type == "one_off":
        return OneOff(first)
    if rule_type == "every":
        return Every(n, unit, first, last)
    return MonthlyOnDay(day, first, last)


def _entry(row: tuple) -> Entry:
    id_, budget_id, kind, name, amount, category_id, source, *rule = row
    return Entry(kind, name, amount, category_id, source, _rule(*rule), id_, budget_id)


def insert(conn: sqlite3.Connection, access: BudgetAccess, draft: Draft) -> Entry:
    """Insert `draft` into the budget and return the stored entry."""
    cursor = conn.execute(
        "INSERT INTO entries (budget_id, kind, name, amount_cents, category_id, source,"
        " rule_type, start_date, end_date, every_n, every_unit, month_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (access.budget_id, draft.kind, draft.name, draft.amount_cents, draft.category_id, draft.source)
        + _rule_columns(draft.rule),
    )
    return Entry(**vars(draft), id=cursor.lastrowid, budget_id=access.budget_id)


def get(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int) -> Entry | None:
    """Return entry `entry_id` of the budget, or None when it is not in this budget."""
    row = conn.execute(
        f"SELECT {_COLUMNS} FROM entries WHERE id = ? AND budget_id = ?", (entry_id, access.budget_id)
    ).fetchone()
    return None if row is None else _entry(row)


def list_for(conn: sqlite3.Connection, access: BudgetAccess) -> list[Entry]:
    """Return every entry of the budget, ordered by id."""
    rows = conn.execute(f"SELECT {_COLUMNS} FROM entries WHERE budget_id = ? ORDER BY id", (access.budget_id,))
    return [_entry(row) for row in rows]


def update(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int, draft: Draft) -> bool:
    """Overwrite the fields of entry `entry_id` with `draft`; False when it is not in this budget."""
    cursor = conn.execute(
        "UPDATE entries SET kind = ?, name = ?, amount_cents = ?, category_id = ?, source = ?,"
        " rule_type = ?, start_date = ?, end_date = ?, every_n = ?, every_unit = ?, month_day = ?"
        " WHERE id = ? AND budget_id = ?",
        (draft.kind, draft.name, draft.amount_cents, draft.category_id, draft.source)
        + _rule_columns(draft.rule)
        + (entry_id, access.budget_id),
    )
    return cursor.rowcount == 1


def delete(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int) -> bool:
    """Delete entry `entry_id` (the whole series); False when it is not in this budget."""
    cursor = conn.execute("DELETE FROM entries WHERE id = ? AND budget_id = ?", (entry_id, access.budget_id))
    return cursor.rowcount == 1
