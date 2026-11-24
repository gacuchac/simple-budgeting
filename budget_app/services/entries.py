"""Entries: create, list, edit a one-off, delete, and edit a recurring entry from a date."""

import datetime as dt
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, replace

from budget_app.domain import recurrence
from budget_app.domain.access import BudgetAccess
from budget_app.domain.recurrence import OneOff, Rule
from budget_app.repos import categories, entries
from budget_app.repos.entries import Draft, Entry

SPLIT_FIELDS = frozenset({"name", "amount_cents", "category_id", "source", "rule"})


class InvalidEntry(ValueError):
    """The entry breaks a rule; the message says which."""


class EntryNotFound(LookupError):
    """The entry is not in this budget."""


@dataclass(frozen=True)
class SplitResult:
    """`previous` is the old entry, ended before the split (None after in-place); `current` applies from it."""

    previous: Entry | None
    current: Entry


def _validate(conn: sqlite3.Connection, access: BudgetAccess, draft: Draft) -> None:
    if draft.amount_cents <= 0:
        raise InvalidEntry("amount_cents must be positive")
    if draft.source is not None and draft.kind != "income":
        raise InvalidEntry("source is only for income")
    if draft.category_id is not None:
        category = categories.get(conn, access, draft.category_id)
        if category is None or category.kind != draft.kind:
            raise InvalidEntry(f"category_id is not a {draft.kind} category of this budget")


def _existing(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int) -> Entry:
    entry = entries.get(conn, access, entry_id)
    if entry is None:
        raise EntryNotFound
    return entry


def create(conn: sqlite3.Connection, access: BudgetAccess, draft: Draft) -> Entry:
    """Validate and store `draft`; raises InvalidEntry for a bad amount, source or category."""
    _validate(conn, access, draft)
    return entries.insert(conn, access, draft)


def list_all(conn: sqlite3.Connection, access: BudgetAccess) -> list[Entry]:
    """Return every entry of the budget."""
    return entries.list_for(conn, access)


def update_one_off(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int, draft: Draft) -> Entry:
    """Replace a one-off entry in place; raises EntryNotFound, or InvalidEntry for a recurring entry or a bad body."""
    entry = _existing(conn, access, entry_id)
    if not isinstance(entry.rule, OneOff):
        raise InvalidEntry("a recurring entry is edited with split")
    if not isinstance(draft.rule, OneOff):
        raise InvalidEntry("a one-off entry stays one-off")
    _validate(conn, access, draft)
    entries.update(conn, access, entry_id, draft)
    return entries.get(conn, access, entry_id)


def remove(conn: sqlite3.Connection, access: BudgetAccess, entry_id: int) -> None:
    """Delete an entry and its whole series; raises EntryNotFound when it is not in the budget."""
    if not entries.delete(conn, access, entry_id):
        raise EntryNotFound


def _changed_draft(entry: Entry, changes: Mapping[str, object]) -> Draft:
    unknown = set(changes) - SPLIT_FIELDS
    if unknown:
        raise InvalidEntry(f"unknown fields: {sorted(unknown)}")
    fields = {key: value for key, value in changes.items() if key != "rule"}
    current = Draft(entry.kind, entry.name, entry.amount_cents, entry.category_id, entry.source, entry.rule)
    return replace(current, **fields)


def _split_rules(entry: Entry, at: dt.date, changes: Mapping[str, object]) -> tuple[Rule | None, Rule]:
    try:
        return recurrence.split(entry.rule, at, changes.get("rule", {}))
    except ValueError as error:
        raise InvalidEntry(str(error)) from None


def split(
    conn: sqlite3.Connection, access: BudgetAccess, entry_id: int, at: dt.date, changes: Mapping[str, object]
) -> SplitResult:
    """Apply `changes` (name, amount_cents, category_id, source, rule) to a recurring entry from `at`.

    In place when `at` is on or before the start; otherwise the old entry ends on `at - 1` and a new one starts on `at`,
    both writes in one transaction. Raises EntryNotFound, or InvalidEntry for a one-off,
    `at` after the end or bad changes.
    """
    entry = _existing(conn, access, entry_id)
    old_rule, new_rule = _split_rules(entry, at, changes)
    draft = replace(_changed_draft(entry, changes), rule=new_rule)
    _validate(conn, access, draft)
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        if old_rule is None:
            entries.update(conn, access, entry_id, draft)
            return SplitResult(None, entries.get(conn, access, entry_id))
        entries.update(conn, access, entry_id, replace(entry, rule=old_rule))
        return SplitResult(entries.get(conn, access, entry_id), entries.insert(conn, access, draft))
