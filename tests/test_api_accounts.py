"""Tests for the accounts and sessions HTTP API."""

import re
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

GOOD = "abcdefg1!"
BAD_EMAILS = ["alice", "alice@", "@x.com", "a b@x.com", "alice@example"]
WEAK = {
    "abcdefgh": ["at least 1 number", "at least 1 special character"],
    "abcdefg1": ["at least 1 special character"],
    "ab1!": ["at least 8 characters"],
}


def make_client(tmp_path: Path) -> TestClient:
    from budget_app.api.app import create_app

    return TestClient(create_app(tmp_path / "app.db"))


@pytest.fixture
def client(tmp_path):
    return make_client(tmp_path)


def rows(tmp_path: Path, sql: str, args: tuple = ()) -> list[tuple]:
    db = sqlite3.connect(tmp_path / "app.db")
    try:
        return db.execute(sql, args).fetchall()
    finally:
        db.close()


def signup(client, email="alice@example.test", password=GOOD):
    return client.post("/api/signup", json={"email": email, "password": password})


def test_us1_signup_returns_201_sets_sid_and_stores_normalised_email(client, tmp_path):
    resp = signup(client, " Alice@Example.Test ")

    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.test"
    assert client.cookies.get("sid")
    assert rows(tmp_path, "SELECT email FROM users") == [("alice@example.test",)]


def test_us1_duplicate_signup_in_any_case_returns_409(client):
    signup(client)

    resp = signup(client, "ALICE@example.test ")

    assert resp.status_code == 409
    assert resp.json() == {"detail": "email already registered"}


@pytest.mark.parametrize("password", list(WEAK))
def test_us1_weak_password_returns_422_naming_the_broken_rules(client, password):
    resp = signup(client, password=password)

    assert resp.status_code == 422
    assert resp.json() == {"detail": WEAK[password]}


@pytest.mark.parametrize("email", BAD_EMAILS)
def test_us1_bad_email_returns_422(client, email):
    resp = signup(client, email)

    assert resp.status_code == 422
    assert resp.json() == {"detail": "invalid email"}


@pytest.mark.parametrize("email", ["bob@team.local", "carol@demo.localhost"])
def test_us1_local_style_emails_are_accepted(client, email):
    assert signup(client, email).status_code == 201


def test_us1_password_is_stored_as_argon2id_and_never_in_the_database_files(client, tmp_path):
    signup(client)

    assert rows(tmp_path, "SELECT pw_hash FROM users")[0][0].startswith("$argon2id$")
    for name in ("app.db", "app.db-wal"):
        path = tmp_path / name
        if path.exists():
            assert GOOD.encode() not in path.read_bytes()


def test_us1_new_account_lists_one_personal_editor_budget_with_default_categories(client, tmp_path):
    signup(client)

    resp = client.get("/api/budgets")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body == [{"id": body[0]["id"], "name": "Personal", "kind": "personal", "role": "editor"}]
    cats = rows(tmp_path, "SELECT kind, COUNT(*) FROM categories WHERE budget_id = ? GROUP BY kind", (body[0]["id"],))
    assert dict(cats) == {"expense": 7, "income": 3}


def test_us2_signin_sets_httponly_lax_400_day_cookie_without_secure(client):
    signup(client)

    resp = TestClient(client.app).post("/api/signin", json={"email": "alice@example.test", "password": GOOD})

    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.test"
    assert_session_cookie(resp.headers["set-cookie"])


def test_us1_signup_sets_the_same_httponly_lax_400_day_cookie_without_secure(client):
    resp = signup(client)

    assert resp.status_code == 201
    assert_session_cookie(resp.headers["set-cookie"])


def assert_session_cookie(header: str) -> None:
    assert header.startswith("sid=")
    assert "httponly" in header.lower()
    assert "samesite=lax" in header.lower()
    assert "Max-Age=34560000" in header
    assert "secure" not in header.lower()


def test_us2_signin_failures_return_identical_401(client):
    signup(client)

    wrong = client.post("/api/signin", json={"email": "alice@example.test", "password": "wrong-pw1!"})
    unknown = client.post("/api/signin", json={"email": "nobody@example.test", "password": GOOD})

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "invalid email or password"}


def test_us2_me_returns_email_with_session_and_401_without_or_with_garbage(client):
    signup(client)

    assert client.get("/api/me").json()["email"] == "alice@example.test"
    assert TestClient(client.app).get("/api/me").status_code == 401
    assert TestClient(client.app).get("/api/me", headers={"Cookie": "sid=garbage"}).status_code == 401


def test_us2_signout_returns_204_and_the_old_sid_is_revoked(client):
    signup(client)
    sid = client.cookies.get("sid")

    resp = client.post("/api/signout")

    assert resp.status_code == 204
    replay = TestClient(client.app).get("/api/me", headers={"Cookie": f"sid={sid}"})
    assert replay.status_code == 401


def test_us2_signout_revokes_only_that_session(client):
    signup(client)
    other = TestClient(client.app)
    other.post("/api/signin", json={"email": "alice@example.test", "password": GOOD})

    client.post("/api/signout")

    assert other.get("/api/me").status_code == 200


def test_us2_sessions_table_holds_only_hashes_never_tokens(client, tmp_path):
    signup(client)
    tokens = [client.cookies.get("sid")]
    other = TestClient(client.app)
    other.post("/api/signin", json={"email": "alice@example.test", "password": GOOD})
    tokens.append(other.cookies.get("sid"))

    hashes = [r[0] for r in rows(tmp_path, "SELECT token_hash FROM sessions")]

    assert len(hashes) == 2
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes)
    assert not set(hashes) & set(tokens)


def test_us2_session_survives_recreating_the_app_on_the_same_file(tmp_path):
    first = make_client(tmp_path)
    signup(first)
    sid = first.cookies.get("sid")

    second = make_client(tmp_path)

    resp = second.get("/api/me", headers={"Cookie": f"sid={sid}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.test"


def test_us2_every_route_except_signup_and_signin_returns_401_without_a_session(client):
    paths = client.app.openapi()["paths"]
    assert {"/api/me", "/api/signout", "/api/budgets"} <= set(paths)
    anonymous = TestClient(client.app)

    checked = 0
    for path, methods in paths.items():
        if path in ("/api/signup", "/api/signin"):
            continue
        url = re.sub(r"\{[^}]+\}", "1", path)
        for method in methods:
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            kwargs = {"json": {}} if method in ("post", "put", "patch") else {}
            resp = anonymous.request(method.upper(), url, **kwargs)
            assert resp.status_code == 401, f"{method.upper()} {path}"
            checked += 1
    assert checked >= 3


def test_us3_budgets_list_excludes_other_users_budgets(client):
    signup(client)
    other = TestClient(client.app)
    other.post("/api/signup", json={"email": "bob@example.test", "password": GOOD})

    mine = client.get("/api/budgets").json()
    theirs = other.get("/api/budgets").json()

    assert len(mine) == len(theirs) == 1
    assert mine[0]["id"] != theirs[0]["id"]


def test_us2_main_serves_the_app_on_loopback_8000(tmp_path, monkeypatch):
    import uvicorn
    from fastapi import FastAPI

    from budget_app.__main__ import main

    db = tmp_path / "x.db"
    monkeypatch.setenv("BUDGET_DB", str(db))
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    main()

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert isinstance(args[0], FastAPI)
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8000
    assert db.exists()
