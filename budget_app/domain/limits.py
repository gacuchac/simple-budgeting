"""Spending limits: calendar periods, pro-rating and the status of a limit over a range."""

import calendar
import datetime as dt
from dataclasses import dataclass
from fractions import Fraction

from budget_app.domain.periods import DateRange, PeriodUnit

_ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Limit:
    """A spending limit of one expense category for its own period."""

    id: int
    budget_id: int
    category_id: int
    amount_cents: int
    period: PeriodUnit


@dataclass(frozen=True)
class LimitStatus:
    """What a limit allows over a range, what was spent, and whether it is over."""

    limit_id: int
    category_id: int
    allowed_cents: int
    spent_cents: int
    over: bool


def period_containing(period: PeriodUnit, d: dt.date) -> DateRange:
    """Return the calendar day, Monday-to-Sunday week, month or year that contains `d`."""
    match period:
        case "day":
            return DateRange(d, d)
        case "week":
            start = d - dt.timedelta(days=d.weekday())
            return DateRange(start, start + dt.timedelta(days=6))
        case "month":
            return DateRange(d.replace(day=1), d.replace(day=calendar.monthrange(d.year, d.month)[1]))
        case "year":
            return DateRange(dt.date(d.year, 1, 1), dt.date(d.year, 12, 31))


def prorate(limit_cents: int, period: PeriodUnit, rng: DateRange) -> int:
    """Return the limit allowed over `rng`: each calendar period it touches counts by its share of days, rounded once."""
    total = Fraction(0)
    day = rng.start
    while day <= rng.end:
        whole = period_containing(period, day)
        overlap = (min(whole.end, rng.end) - day).days + 1
        total += Fraction(limit_cents * overlap, (whole.end - whole.start).days + 1)
        day = whole.end + _ONE_DAY
    return round(total)


def limit_status(limit: Limit, rng: DateRange, spent_cents: int) -> LimitStatus:
    """Return the status of `limit` over `rng` given the cents spent there; over means spent exceeds allowed."""
    allowed = prorate(limit.amount_cents, limit.period, rng)
    return LimitStatus(limit.id, limit.category_id, allowed, spent_cents, spent_cents > allowed)
