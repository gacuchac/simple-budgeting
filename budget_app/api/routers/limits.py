"""Spending limits of a budget and the over-limit check for the expense form."""

import datetime as dt
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from budget_app.api.deps import Conn, EditAccess, ViewAccess
from budget_app.api.schemas import LimitCheckOut, LimitIn, LimitOut, LimitStatusOut
from budget_app.domain.limits import Limit
from budget_app.services import limits

router = APIRouter(prefix="/api/budgets/{budget_id}/limits")


def _out(limit: Limit) -> LimitOut:
    return LimitOut(**asdict(limit))


@router.get("")
def list_limits(access: ViewAccess, conn: Conn) -> list[LimitOut]:
    """Return the budget's limits."""
    return [_out(lim) for lim in limits.list_all(conn, access)]


@router.put("")
def set_limit(body: LimitIn, access: EditAccess, conn: Conn) -> LimitOut:
    """Set the limit of an expense category, replacing its old one; 404 for an unknown category, 422 for income."""
    try:
        return _out(limits.set_limit(conn, access, body.category_id, body.amount_cents, body.period))
    except limits.LimitNotFound:
        raise HTTPException(404) from None
    except limits.InvalidLimit as error:
        raise HTTPException(422, str(error)) from None


@router.get("/check")
def check_limit(
    access: ViewAccess,
    conn: Conn,
    category_id: int,
    on: Annotated[dt.date, Query(alias="date")],
    amount_cents: int,
    exclude_entry_id: int | None = None,
) -> LimitCheckOut:
    """Return `{status}`: the category's limit over its own period containing `date` with `amount_cents` added.

    `status` is null without a limit; 422 for a bad category, entry, amount or date.
    """
    try:
        status = limits.check(conn, access, category_id, on, amount_cents, exclude_entry_id)
    except limits.InvalidLimit as error:
        raise HTTPException(422, str(error)) from None
    return LimitCheckOut(status=None if status is None else LimitStatusOut(**asdict(status)))


@router.delete("/{limit_id}", status_code=204)
def delete_limit(limit_id: int, access: EditAccess, conn: Conn) -> Response:
    """Delete a limit; 404 when it is not in the budget."""
    try:
        limits.remove(conn, access, limit_id)
    except limits.LimitNotFound:
        raise HTTPException(404) from None
    return Response(status_code=204)
