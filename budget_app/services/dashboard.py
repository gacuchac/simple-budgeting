"""The dashboard: totals, donut and cumulative lines for a period."""

import datetime as dt
import sqlite3
from dataclasses import dataclass

from budget_app.domain import periods
from budget_app.domain.access import BudgetAccess
from budget_app.domain.dashboard import (
    BucketUnit,
    Donut,
    Point,
    Slice,
    bucket_unit,
    cumulative,
    donut,
)
from budget_app.domain.periods import DateRange, PeriodSpec
from budget_app.domain.recurrence import occurrences
from budget_app.repos import categories, entries
from budget_app.repos.entries import Entry

UNCATEGORIZED = "Uncategorized"


@dataclass(frozen=True)
class Dashboard:
    """Everything the dashboard shows for one range."""

    range: DateRange
    income_cents: int
    expense_cents: int
    donut: Donut
    unit: BucketUnit
    income_points: list[Point]
    expense_points: list[Point]


def _events(all_entries: list[Entry], kind: str, rng: DateRange) -> list[tuple[dt.date, int, int | None]]:
    return [
        (day, e.amount_cents, e.category_id)
        for e in all_entries
        if e.kind == kind
        for day in occurrences(e.rule, rng.start, rng.end)
    ]


def _slices(expenses: list[tuple[dt.date, int, int | None]], names: dict[int, str]) -> list[Slice]:
    totals: dict[int | None, int] = {}
    for _, cents, category_id in expenses:
        totals[category_id] = totals.get(category_id, 0) + cents
    ordered = sorted(totals, key=lambda c: (c is None, c))
    return [Slice(c, UNCATEGORIZED if c is None else names[c], totals[c]) for c in ordered]


def build(conn: sqlite3.Connection, access: BudgetAccess, spec: PeriodSpec, today: dt.date) -> Dashboard:
    """Build the dashboard for `spec` resolved against `today`; raises ValueError for an invalid period."""
    rng = periods.resolve(spec, today)
    all_entries = entries.list_for(conn, access)
    income = _events(all_entries, "income", rng)
    expenses = _events(all_entries, "expense", rng)
    names = {c.id: c.name for c in categories.list_for(conn, access)}
    income_cents = sum(cents for _, cents, _ in income)
    return Dashboard(
        range=rng,
        income_cents=income_cents,
        expense_cents=sum(cents for _, cents, _ in expenses),
        donut=donut(income_cents, _slices(expenses, names)),
        unit=bucket_unit(rng),
        income_points=cumulative([(d, c) for d, c, _ in income], rng),
        expense_points=cumulative([(d, c) for d, c, _ in expenses], rng),
    )
