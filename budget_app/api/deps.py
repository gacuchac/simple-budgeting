"""Request dependencies: the per-request connection, the signed-in user and the budget guard."""

import sqlite3
from collections.abc import Callable, Iterator
from typing import Annotated, Literal

from fastapi import Cookie, Depends, HTTPException, Request

from budget_app.auth import sessions
from budget_app.db.connection import connect
from budget_app.domain.access import BudgetAccess
from budget_app.repos import members
from budget_app.repos.users import UserId


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    """Yield a connection to the app's database and close it after the request."""
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
Sid = Annotated[str | None, Cookie()]


def current_user(conn: Conn, sid: Sid = None) -> UserId:
    """Return the user of the `sid` cookie; respond 401 when it is missing or invalid."""
    user_id = sessions.resolve(conn, sid) if sid else None
    if user_id is None:
        raise HTTPException(401)
    return user_id


CurrentUser = Annotated[UserId, Depends(current_user)]


def budget_access(need: Literal["view", "edit"]) -> Callable[..., BudgetAccess]:
    """Return a dependency that resolves the caller's access to the path's `budget_id`.

    Responds 404 to a non-member, and 403 when `need` is "edit" and the caller is a viewer.
    """

    def guard(budget_id: int, user_id: CurrentUser, conn: Conn) -> BudgetAccess:
        access = members.access_for(conn, budget_id, user_id)
        if access is None:
            raise HTTPException(404)
        if need == "edit" and access.role != "editor":
            raise HTTPException(403)
        return access

    guard.is_budget_guard = True
    return guard


ViewAccess = Annotated[BudgetAccess, Depends(budget_access("view"))]
EditAccess = Annotated[BudgetAccess, Depends(budget_access("edit"))]
