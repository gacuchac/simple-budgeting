"""US-2: split keeps the past, edits in place, and refuses bad input. Plus domain purity."""

import ast
import importlib
from datetime import date as D
from pathlib import Path

import pytest

DOMAIN = Path(__file__).resolve().parent.parent / "budget_app" / "domain"
ALLOWED = {"__future__", "calendar", "collections.abc", "dataclasses", "datetime", "re", "typing"}


def _rec():
    return importlib.import_module("budget_app.domain.recurrence")


def test_us2_split_keeps_the_past():
    rec = _rec()
    rule = rec.Every(1, "month", D(2026, 1, 31))
    old, new = rec.split(rule, D(2026, 6, 1), {"n": 2})
    lo, hi = D(2026, 1, 1), D(2026, 12, 31)
    before = [d for d in rec.occurrences(rule, lo, hi) if d < D(2026, 6, 1)]
    assert rec.occurrences(old, lo, hi) == before
    new_dates = rec.occurrences(new, lo, hi)
    assert new_dates[0] == D(2026, 6, 1)
    assert all(d >= D(2026, 6, 1) for d in new_dates)


@pytest.mark.parametrize("at", [D(2026, 3, 1), D(2026, 2, 1)])
def test_us2_split_at_or_before_start_edits_in_place(at):
    rec = _rec()
    rule = rec.Every(1, "week", D(2026, 3, 1))
    assert rec.split(rule, at, {"n": 3}) == (None, rec.Every(3, "week", D(2026, 3, 1)))


def test_us2_split_changes_can_move_start_in_place():
    rec = _rec()
    rule = rec.Every(1, "week", D(2026, 3, 1))
    got = rec.split(rule, D(2026, 3, 1), {"start": D(2026, 4, 1)})
    assert got == (None, rec.Every(1, "week", D(2026, 4, 1)))


def test_us2_split_keeps_end_on_new_rule():
    rec = _rec()
    rule = rec.MonthlyOnDay(5, D(2026, 1, 5), D(2026, 12, 5))
    old, new = rec.split(rule, D(2026, 6, 1), {"day": 10})
    assert old == rec.MonthlyOnDay(5, D(2026, 1, 5), D(2026, 5, 31))
    assert new == rec.MonthlyOnDay(10, D(2026, 6, 1), D(2026, 12, 5))


def test_us2_split_at_end_is_allowed_and_after_end_refused():
    rec = _rec()
    rule = rec.MonthlyOnDay(5, D(2026, 1, 5), D(2026, 12, 5))
    old, new = rec.split(rule, D(2026, 12, 5), {"day": 6})
    assert old.end == D(2026, 12, 4)
    assert new.start == D(2026, 12, 5)
    with pytest.raises(ValueError):
        rec.split(rule, D(2026, 12, 6), {"day": 6})


def test_us2_split_can_change_shape():
    rec = _rec()
    rule = rec.MonthlyOnDay(1, D(2026, 1, 1))
    old, new = rec.split(rule, D(2026, 6, 1), rec.Every(4, "week", D(2020, 1, 1)))
    assert old == rec.MonthlyOnDay(1, D(2026, 1, 1), D(2026, 5, 31))
    assert new == rec.Every(4, "week", D(2026, 6, 1))


def test_us2_split_shape_change_in_place_returns_replacement_as_given():
    rec = _rec()
    rule = rec.MonthlyOnDay(1, D(2026, 6, 1))
    repl = rec.Every(4, "week", D(2020, 1, 1))
    assert rec.split(rule, D(2026, 6, 1), repl) == (None, repl)


def test_us2_split_refuses_one_off_replacement():
    rec = _rec()
    rule = rec.Every(1, "day", D(2026, 1, 1))
    with pytest.raises(ValueError):
        rec.split(rule, D(2026, 6, 1), rec.OneOff(D(2026, 7, 1)))


def test_us2_split_refuses_one_off_rule():
    rec = _rec()
    with pytest.raises(ValueError):
        rec.split(rec.OneOff(D(2026, 1, 1)), D(2026, 1, 1), {})


def test_us2_split_unknown_field_raises_type_error():
    rec = _rec()
    with pytest.raises(TypeError):
        rec.split(rec.Every(1, "day", D(2026, 1, 1)), D(2026, 6, 1), {"nope": 1})


def test_us2_split_revalidates_changes():
    rec = _rec()
    with pytest.raises(ValueError):
        rec.split(rec.Every(1, "day", D(2026, 1, 1)), D(2026, 6, 1), {"n": 0})


def test_us2_domain_modules_are_pure():
    for name in ("money", "accounts", "recurrence"):
        path = DOMAIN / f"{name}.py"
        assert path.exists(), path
        src = path.read_text()
        assert "today(" not in src
        assert "now(" not in src
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            else:
                continue
            assert set(mods) <= ALLOWED, (name, mods)
