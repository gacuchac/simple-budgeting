"""Dashboard maths: the donut and the cumulative lines."""

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from budget_app.domain.periods import DateRange

BucketUnit = Literal["day", "week", "month"]
_ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Slice:
    """Expense total of one category (None is uncategorized)."""

    category_id: int | None
    name: str
    amount_cents: int


@dataclass(frozen=True)
class Donut:
    """The ring: `total_cents` is income, or expenses when they exceed it, then `mark_cents` is the income."""

    total_cents: int
    slices: tuple[Slice, ...]
    remaining_cents: int
    mark_cents: int | None


@dataclass(frozen=True)
class Point:
    """Cumulative cents at the end of the bucket starting `date`."""

    date: dt.date
    cents: int


def donut(income_cents: int, by_category: Sequence[Slice]) -> Donut:
    """Build the donut from the income total and the expense slices; all zero gives an empty donut."""
    slices = tuple(by_category)
    expense = sum(s.amount_cents for s in slices)
    if expense > income_cents:
        return Donut(expense, slices, 0, income_cents)
    return Donut(income_cents, slices, income_cents - expense, None)


def bucket_unit(rng: DateRange) -> BucketUnit:
    """Return day for a range of up to 62 days, week for up to 366 days, else month."""
    days = (rng.end - rng.start).days + 1
    return "day" if days <= 62 else "week" if days <= 366 else "month"


def _next_start(d: dt.date, unit: BucketUnit) -> dt.date:
    match unit:
        case "day":
            return d + _ONE_DAY
        case "week":
            return d + dt.timedelta(days=7 - d.weekday())
        case "month":
            return (d.replace(day=1) + dt.timedelta(days=32)).replace(day=1)


def _bucket_starts(rng: DateRange, unit: BucketUnit) -> list[dt.date]:
    starts = [rng.start]
    while (nxt := _next_start(starts[-1], unit)) <= rng.end:
        starts.append(nxt)
    return starts


def cumulative(events: Sequence[tuple[dt.date, int]], rng: DateRange) -> list[Point]:
    """Return the running total of `events` (date, cents) at the end of each bucket of `rng`.

    Buckets follow `bucket_unit` (weeks start on Monday); events outside the range are ignored,
    and the last point is the total inside the range.
    """
    starts = _bucket_starts(rng, bucket_unit(rng))
    ends = [s - _ONE_DAY for s in starts[1:]] + [rng.end]
    inside = sorted(e for e in events if rng.start <= e[0] <= rng.end)
    points: list[Point] = []
    total = i = 0
    for start, end in zip(starts, ends, strict=True):
        while i < len(inside) and inside[i][0] <= end:
            total += inside[i][1]
            i += 1
        points.append(Point(start, total))
    return points
