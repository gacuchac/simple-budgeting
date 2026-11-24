"""Periods: the inclusive date range a dashboard covers."""

import calendar
import datetime as dt
from dataclasses import dataclass
from typing import Literal

PeriodUnit = Literal["day", "week", "month", "year"]
_ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class DateRange:
    """Inclusive range of dates."""

    start: dt.date
    end: dt.date


@dataclass(frozen=True)
class Last:
    """The last `n` `unit`s, ending today."""

    n: int
    unit: PeriodUnit


@dataclass(frozen=True)
class Range:
    """A calendar range, both ends inclusive."""

    start: dt.date
    end: dt.date


PeriodSpec = Last | Range


def _months_back(d: dt.date, months: int) -> dt.date:
    year, month = divmod(d.year * 12 + d.month - 1 - months, 12)
    month += 1
    return dt.date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _back(today: dt.date, n: int, unit: PeriodUnit) -> dt.date:
    match unit:
        case "day":
            return today - dt.timedelta(days=n)
        case "week":
            return today - dt.timedelta(weeks=n)
        case "month":
            return _months_back(today, n)
        case "year":
            return _months_back(today, 12 * n)


def resolve(spec: PeriodSpec, today: dt.date) -> DateRange:
    """Return the date range of `spec`; `Last(n, unit)` ends `today` and starts the day after `n` units back.

    Raises ValueError for n < 1, or a Range that ends before it starts.
    """
    match spec:
        case Last(n=n, unit=unit):
            if n < 1:
                raise ValueError("n must be at least 1")
            return DateRange(_back(today, n, unit) + _ONE_DAY, today)
        case Range(start=start, end=end):
            if end < start:
                raise ValueError("end must not be before start")
            return DateRange(start, end)
