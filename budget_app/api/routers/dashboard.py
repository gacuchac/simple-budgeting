"""The dashboard of a budget."""

import datetime as dt
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, HTTPException

from budget_app.api.deps import Conn, ViewAccess
from budget_app.api.schemas import (
    DashboardOut,
    DonutOut,
    LimitStatusOut,
    LinesOut,
    PointOut,
    RangeOut,
    SliceOut,
)
from budget_app.domain.periods import Last, PeriodSpec, Range
from budget_app.services import dashboard

router = APIRouter(prefix="/api/budgets/{budget_id}/dashboard")


def _spec(
    last: int | None, unit: Literal["day", "week", "month", "year"] | None, start: dt.date | None, end: dt.date | None
) -> PeriodSpec:
    if last is not None and unit is not None and start is None and end is None:
        return Last(last, unit)
    if start is not None and end is not None and last is None and unit is None:
        return Range(start, end)
    raise HTTPException(422, "give either last and unit, or start and end")


def _out(board: dashboard.Dashboard) -> DashboardOut:
    d = board.donut
    points = [
        PointOut(date=i.date, income_cum=i.cents, expense_cum=e.cents)
        for i, e in zip(board.income_points, board.expense_points, strict=True)
    ]
    return DashboardOut(
        range=RangeOut(start=board.range.start, end=board.range.end),
        income_cents=board.income_cents,
        expense_cents=board.expense_cents,
        donut=DonutOut(
            total_cents=d.total_cents,
            slices=[SliceOut(category_id=s.category_id, name=s.name, amount_cents=s.amount_cents) for s in d.slices],
            remaining_cents=d.remaining_cents,
            mark_cents=d.mark_cents,
        ),
        lines=LinesOut(unit=board.unit, points=points),
        limits=[LimitStatusOut(**asdict(s)) for s in board.limits],
    )


@router.get("")
def get_dashboard(
    access: ViewAccess,
    conn: Conn,
    last: int | None = None,
    unit: Literal["day", "week", "month", "year"] | None = None,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> DashboardOut:
    """Return the dashboard for `?last=&unit=` or `?start=&end=`, "today" being the local date; 422 for a bad period."""
    spec = _spec(last, unit, start, end)
    try:
        return _out(dashboard.build(conn, access, spec, dt.date.today()))
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
