"""Sign-up, sign-in, sign-out and the current account."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response

from budget_app.api.deps import Conn, CurrentUser, Sid, current_user
from budget_app.api.schemas import AccountOut, Credentials
from budget_app.auth import sessions
from budget_app.repos.users import UserId
from budget_app.services import accounts

router = APIRouter(prefix="/api")

COOKIE_MAX_AGE = 34560000


def _account_out(conn: sqlite3.Connection, user_id: UserId) -> AccountOut:
    acct = accounts.account(conn, user_id)
    return AccountOut(id=acct.id, email=acct.email)


def _start_session(conn: sqlite3.Connection, response: Response, user_id: UserId) -> AccountOut:
    token = sessions.start(conn, user_id)
    response.set_cookie("sid", token, max_age=COOKIE_MAX_AGE, httponly=True, samesite="lax", secure=False, path="/")
    return _account_out(conn, user_id)


@router.post("/signup", status_code=201)
def signup(body: Credentials, response: Response, conn: Conn) -> AccountOut:
    """Create an account and sign it in; 422 for a bad email or weak password, 409 for a taken email."""
    try:
        user_id = accounts.sign_up(conn, body.email, body.password)
    except accounts.InvalidEmail:
        raise HTTPException(422, "invalid email") from None
    except accounts.WeakPassword as weak:
        raise HTTPException(422, weak.problems) from None
    except accounts.EmailTaken:
        raise HTTPException(409, "email already registered") from None
    return _start_session(conn, response, user_id)


@router.post("/signin")
def signin(body: Credentials, response: Response, conn: Conn) -> AccountOut:
    """Sign in; 401 with one message for every failure."""
    user_id = accounts.sign_in(conn, body.email, body.password)
    if user_id is None:
        raise HTTPException(401, "invalid email or password")
    return _start_session(conn, response, user_id)


@router.post("/signout", status_code=204, dependencies=[Depends(current_user)])
def signout(conn: Conn, sid: Sid = None) -> Response:
    """Revoke the current session and clear the cookie."""
    sessions.end(conn, sid)
    response = Response(status_code=204)
    response.delete_cookie("sid", path="/")
    return response


@router.get("/me")
def me(user_id: CurrentUser, conn: Conn) -> AccountOut:
    """Return the signed-in account."""
    return _account_out(conn, user_id)
