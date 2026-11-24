"""Recurrence rules: the dates they expand to, and splitting a rule at a date."""

from __future__ import annotations

import calendar
import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal

Unit = Literal["day", "week", "month"]
_UNITS = ("day", "week", "month")
_ONE_DAY = dt.timedelta(days=1)


def _check_end(start: dt.date, end: dt.date | None) -> None:
    if end is not None and end < start:
        raise ValueError("end must not be before start")


@dataclass(frozen=True)
class OneOff:
    """A single occurrence on `date`."""

    date: dt.date


@dataclass(frozen=True)
class Every:
    """Every `n` `unit`s from `start` to `end` (inclusive, optional)."""

    n: int
    unit: Unit
    start: dt.date
    end: dt.date | None = None

    def __post_init__(self) -> None:
        """Raise ValueError for n < 1, an unknown unit, or end before start."""
        if self.n < 1:
            raise ValueError("n must be at least 1")
        if self.unit not in _UNITS:
            raise ValueError(f"unknown unit: {self.unit!r}")
        _check_end(self.start, self.end)


@dataclass(frozen=True)
class MonthlyOnDay:
    """Every month on `day` (clamped to the month's end), from `start` to `end`."""

    day: int
    start: dt.date
    end: dt.date | None = None

    def __post_init__(self) -> None:
        """Raise ValueError for a day outside 1..31 or end before start."""
        if not 1 <= self.day <= 31:
            raise ValueError("day must be between 1 and 31")
        _check_end(self.start, self.end)


Rule = OneOff | Every | MonthlyOnDay


def _add_months(first: dt.date, months: int, anchor_day: int) -> dt.date:
    year, month = divmod(first.month - 1 + months, 12)
    year, month = first.year + year, month + 1
    return dt.date(year, month, min(anchor_day, calendar.monthrange(year, month)[1]))


def _monthly(
    first: dt.date, step: int, anchor_day: int, lo: dt.date, stop: dt.date
) -> list[dt.date]:
    out: list[dt.date] = []
    k = 0
    while (d := _add_months(first, k * step, anchor_day)) <= stop:
        if d >= lo:
            out.append(d)
        k += 1
    return out


def _stepped(rule: Every, lo: dt.date, stop: dt.date) -> list[dt.date]:
    step = rule.n * (7 if rule.unit == "week" else 1)
    skipped = -(-(lo - rule.start).days // step) if lo > rule.start else 0
    d = rule.start + dt.timedelta(days=skipped * step)
    out: list[dt.date] = []
    while d <= stop:
        out.append(d)
        d += dt.timedelta(days=step)
    return out


def _every(rule: Every, lo: dt.date, stop: dt.date) -> list[dt.date]:
    if rule.unit == "month":
        return _monthly(rule.start, rule.n, rule.start.day, lo, stop)
    return _stepped(rule, lo, stop)


def occurrences(rule: Rule, lo: dt.date, hi: dt.date) -> list[dt.date]:
    """Return the sorted dates of `rule` in [lo, hi], both ends and the rule's `end` inclusive.

    Month steps anchor on the rule's own day and clamp to the month's last day.
    `lo > hi` gives an empty list.
    """
    if lo > hi:
        return []
    if isinstance(rule, OneOff):
        return [rule.date] if lo <= rule.date <= hi else []
    stop = hi if rule.end is None else min(hi, rule.end)
    if isinstance(rule, MonthlyOnDay):
        first = dt.date(rule.start.year, rule.start.month, 1)
        return _monthly(first, 1, rule.day, max(lo, rule.start), stop)
    return _every(rule, lo, stop)


def _apply_changes(
    rule: Every | MonthlyOnDay, at: dt.date, changes: Mapping[str, object] | Rule, in_place: bool
) -> Rule:
    match changes:
        case OneOff():
            raise ValueError("a split cannot turn a rule into a one-off")
        case Every() | MonthlyOnDay():
            return changes if in_place else replace(changes, start=at)
        case _:
            return replace(rule, **changes) if in_place else replace(rule, **{**changes, "start": at})


def split(rule: Rule, at: dt.date, changes: Mapping[str, object] | Rule) -> tuple[Rule | None, Rule]:
    """Change a recurring rule from `at` onward; return `(old, new)`.

    `changes` is a mapping of field overrides, or a replacement recurring rule.
    When `at <= rule.start` the rule is edited in place and `old` is None.
    Otherwise `old` is the rule ended the day before `at` and `new` starts on `at`.
    Raises ValueError for a OneOff rule or replacement, or for `at` after the rule's end,
    and TypeError for an unknown field in `changes`.
    """
    match rule:
        case OneOff():
            raise ValueError("a one-off rule cannot be split")
    if rule.end is not None and at > rule.end:
        raise ValueError("at is after the rule's end")
    in_place = at <= rule.start
    new = _apply_changes(rule, at, changes, in_place)
    return (None if in_place else replace(rule, end=at - _ONE_DAY)), new
