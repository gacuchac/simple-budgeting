"""Request dependencies: the per-request connection and the signed-in user."""

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request

from budget_app.auth import sessions
from budget_app.db.connection import connect
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
