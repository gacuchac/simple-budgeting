"""US-2: rule shapes and occurrences."""

import importlib
from datetime import date as D

import pytest


def _rec():
    return importlib.import_module("budget_app.domain.recurrence")


def _build(spec):
    kind, kwargs = spec
    return getattr(_rec(), kind)(**kwargs)


ALL_2026 = (D(2026, 1, 1), D(2026, 12, 31))


def _md(pairs, year=2026):
    return [D(year, m, d) for m, d in pairs]


CASES = [
    (
        "dom31_all_months",
        ("MonthlyOnDay", {"day": 31, "start": D(2026, 1, 1)}),
        *ALL_2026,
        _md([(1, 31), (2, 28), (3, 31), (4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31), (11, 30), (12, 31)]),
    ),
    (
        "interval_month_from_31",
        ("Every", {"n": 1, "unit": "month", "start": D(2026, 1, 31)}),
        D(2026, 1, 1),
        D(2026, 5, 31),
        [D(2026, 1, 31), D(2026, 2, 28), D(2026, 3, 31), D(2026, 4, 30), D(2026, 5, 31)],
    ),
    (
        "dom30_feb",
        ("MonthlyOnDay", {"day": 30, "start": D(2026, 1, 1)}),
        D(2026, 1, 1),
        D(2026, 3, 31),
        [D(2026, 1, 30), D(2026, 2, 28), D(2026, 3, 30)],
    ),
    (
        "leap_every_12_months",
        ("Every", {"n": 12, "unit": "month", "start": D(2028, 2, 29)}),
        D(2028, 1, 1),
        D(2032, 12, 31),
        [D(2028, 2, 29), D(2029, 2, 28), D(2030, 2, 28), D(2031, 2, 28), D(2032, 2, 29)],
    ),
    (
        "biweekly_across_edges",
        ("Every", {"n": 2, "unit": "week", "start": D(2026, 1, 1)}),
        D(2026, 1, 10),
        D(2026, 2, 12),
        [D(2026, 1, 15), D(2026, 1, 29), D(2026, 2, 12)],
    ),
    (
        "end_date_inclusive",
        ("MonthlyOnDay", {"day": 5, "start": D(2026, 1, 5), "end": D(2026, 3, 5)}),
        *ALL_2026,
        [D(2026, 1, 5), D(2026, 2, 5), D(2026, 3, 5)],
    ),
    (
        "start_before_range",
        ("MonthlyOnDay", {"day": 5, "start": D(2025, 11, 5)}),
        D(2026, 1, 1),
        D(2026, 2, 28),
        [D(2026, 1, 5), D(2026, 2, 5)],
    ),
    (
        "dom_start_after_day",
        ("MonthlyOnDay", {"day": 5, "start": D(2026, 1, 10)}),
        D(2026, 1, 1),
        D(2026, 3, 31),
        [D(2026, 2, 5), D(2026, 3, 5)],
    ),
    (
        "every_3_days",
        ("Every", {"n": 3, "unit": "day", "start": D(2026, 2, 26)}),
        D(2026, 2, 26),
        D(2026, 3, 8),
        [D(2026, 2, 26), D(2026, 3, 1), D(2026, 3, 4), D(2026, 3, 7)],
    ),
    (
        "weekly_range_edge_exact",
        ("Every", {"n": 1, "unit": "week", "start": D(2026, 1, 1)}),
        D(2026, 1, 8),
        D(2026, 1, 22),
        [D(2026, 1, 8), D(2026, 1, 15), D(2026, 1, 22)],
    ),
    (
        "rule_ends_before_range",
        ("MonthlyOnDay", {"day": 1, "start": D(2025, 1, 1), "end": D(2025, 12, 31)}),
        *ALL_2026,
        [],
    ),
    (
        "rule_starts_after_range",
        ("MonthlyOnDay", {"day": 1, "start": D(2027, 1, 1)}),
        *ALL_2026,
        [],
    ),
    (
        "every_2_months_from_31",
        ("Every", {"n": 2, "unit": "month", "start": D(2026, 8, 31)}),
        D(2026, 8, 1),
        D(2027, 4, 30),
        [D(2026, 8, 31), D(2026, 10, 31), D(2026, 12, 31), D(2027, 2, 28), D(2027, 4, 30)],
    ),
    (
        "dom29_leap_year",
        ("MonthlyOnDay", {"day": 29, "start": D(2028, 1, 1)}),
        D(2028, 2, 1),
        D(2028, 2, 29),
        [D(2028, 2, 29)],
    ),
    (
        "single_day_range",
        ("Every", {"n": 1, "unit": "day", "start": D(2026, 1, 1)}),
        D(2026, 6, 15),
        D(2026, 6, 15),
        [D(2026, 6, 15)],
    ),
    (
        "dst_week_newyork",
        ("Every", {"n": 1, "unit": "week", "start": D(2026, 3, 1)}),
        D(2026, 3, 1),
        D(2026, 3, 29),
        [D(2026, 3, d) for d in (1, 8, 15, 22, 29)],
    ),
]


@pytest.mark.parametrize(
    ("spec", "lo", "hi", "want"), [c[1:] for c in CASES], ids=[c[0] for c in CASES]
)
def test_us2_occurrences_golden_table(spec, lo, hi, want):
    assert _rec().occurrences(_build(spec), lo, hi) == want


@pytest.mark.parametrize(
    ("lo", "hi", "want"),
    [
        (D(2026, 5, 1), D(2026, 5, 31), [D(2026, 5, 10)]),
        (D(2026, 5, 10), D(2026, 5, 20), [D(2026, 5, 10)]),
        (D(2026, 5, 1), D(2026, 5, 10), [D(2026, 5, 10)]),
        (D(2026, 5, 11), D(2026, 5, 31), []),
        (D(2026, 4, 1), D(2026, 5, 9), []),
    ],
)
def test_us2_one_off_occurs_only_inside_range(lo, hi, want):
    rec = _rec()
    assert rec.occurrences(rec.OneOff(D(2026, 5, 10)), lo, hi) == want


def test_us2_occurrences_empty_when_lo_after_hi():
    rec = _rec()
    rule = rec.Every(1, "day", D(2026, 1, 1))
    assert rec.occurrences(rule, D(2026, 2, 1), D(2026, 1, 1)) == []


@pytest.mark.parametrize(
    "spec",
    [
        ("Every", {"n": 0, "unit": "day", "start": D(2026, 1, 1)}),
        ("Every", {"n": 1, "unit": "year", "start": D(2026, 1, 1)}),
        ("Every", {"n": 1, "unit": "day", "start": D(2026, 1, 2), "end": D(2026, 1, 1)}),
        ("MonthlyOnDay", {"day": 0, "start": D(2026, 1, 1)}),
        ("MonthlyOnDay", {"day": 32, "start": D(2026, 1, 1)}),
        ("MonthlyOnDay", {"day": 5, "start": D(2026, 1, 2), "end": D(2026, 1, 1)}),
    ],
)
def test_us2_invalid_rules_raise_value_error(spec):
    with pytest.raises(ValueError):
        _build(spec)
