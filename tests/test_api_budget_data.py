"""Happy-path tests for the categories, entries and dashboard routes and the budget guard."""

import datetime as dt
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from budget_app.api.app import create_app

PASSWORD = "abcdefg1!"


@pytest.fixture
def app(tmp_path: Path):
    return create_app(tmp_path / "app.db")


def sign_up(app, email: str) -> TestClient:
    client = TestClient(app)
    assert client.post("/api/signup", json={"email": email, "password": PASSWORD}).status_code == 201
    return client


@pytest.fixture
def client(app) -> TestClient:
    return sign_up(app, "alice@example.test")


@pytest.fixture
def base(client) -> str:
    return f"/api/budgets/{client.get('/api/budgets').json()[0]['id']}"


def category_id(client, base: str, kind: str, name: str) -> int:
    return next(c["id"] for c in client.get(f"{base}/categories").json() if (c["kind"], c["name"]) == (kind, name))


def entry_body(**over) -> dict:
    body = {
        "kind": "expense",
        "name": "Rent",
        "amount_cents": 1000,
        "category_id": None,
        "source": None,
        "rule": {"type": "every", "n": 1, "unit": "month", "start": "2026-01-01", "end": None},
    }
    return body | over


def one_off(day: str) -> dict:
    return {"type": "one_off", "date": day}


def test_categories_list_add_rename_delete(client, base):
    assert len(client.get(f"{base}/categories").json()) == 10

    added = client.post(f"{base}/categories", json={"kind": "expense", "name": "Pets"})
    assert added.status_code == 201
    assert client.post(f"{base}/categories", json={"kind": "expense", "name": "Pets"}).status_code == 409

    renamed = client.put(f"{base}/categories/{added.json()['id']}", json={"name": "Animals"})
    assert renamed.json()["name"] == "Animals"
    assert client.delete(f"{base}/categories/{added.json()['id']}").status_code == 204
    assert client.delete(f"{base}/categories/{added.json()['id']}").status_code == 404


def test_entries_create_list_put_delete(client, base):
    food = category_id(client, base, "expense", "Food")
    created = client.post(f"{base}/entries", json=entry_body(category_id=food, rule=one_off("2026-03-01")))
    assert created.status_code == 201
    entry_id = created.json()["id"]
    assert client.get(f"{base}/entries").json() == [created.json()]

    put = client.put(f"{base}/entries/{entry_id}", json=entry_body(amount_cents=500, rule=one_off("2026-03-02")))
    assert put.json()["amount_cents"] == 500
    assert put.json()["rule"] == one_off("2026-03-02")

    assert client.delete(f"{base}/entries/{entry_id}").status_code == 204
    assert client.get(f"{base}/entries").json() == []


def test_entry_validation_returns_422(client, base):
    salary = category_id(client, base, "income", "Salary")
    assert client.post(f"{base}/entries", json=entry_body(amount_cents=0)).status_code == 422
    assert client.post(f"{base}/entries", json=entry_body(category_id=salary)).status_code == 422
    assert client.post(f"{base}/entries", json=entry_body(source="Acme")).status_code == 422


def test_split_from_a_date_ends_old_entry_and_starts_new(client, base):
    entry_id = client.post(f"{base}/entries", json=entry_body()).json()["id"]

    resp = client.post(f"{base}/entries/{entry_id}/split", json={"at": "2026-06-01", "changes": {"amount_cents": 1200}})

    assert resp.status_code == 201
    previous, current = resp.json()["previous"], resp.json()["current"]
    assert previous["id"] == entry_id
    assert previous["rule"]["end"] == "2026-05-31"
    assert current["amount_cents"] == 1200
    assert current["rule"]["start"] == "2026-06-01"
    assert len(client.get(f"{base}/entries").json()) == 2


def test_split_before_start_updates_in_place_and_after_end_is_422(client, base):
    entry_id = client.post(f"{base}/entries", json=entry_body()).json()["id"]
    resp = client.post(f"{base}/entries/{entry_id}/split", json={"at": "2025-01-01", "changes": {"name": "Flat"}})
    assert resp.json()["previous"] is None
    assert resp.json()["current"]["id"] == entry_id

    ended = entry_body(rule={"type": "every", "n": 1, "unit": "month", "start": "2026-01-01", "end": "2026-03-01"})
    ended_id = client.post(f"{base}/entries", json=ended).json()["id"]
    assert client.post(f"{base}/entries/{ended_id}/split", json={"at": "2026-04-01", "changes": {}}).status_code == 422

    one = client.post(f"{base}/entries", json=entry_body(rule=one_off("2026-03-01"))).json()["id"]
    assert client.post(f"{base}/entries/{one}/split", json={"at": "2026-03-01", "changes": {}}).status_code == 422


def test_dashboard_totals_donut_and_lines(client, base):
    food = category_id(client, base, "expense", "Food")
    pay = entry_body(kind="income", name="Pay", amount_cents=5000, rule=one_off("2026-03-05"))
    client.post(f"{base}/entries", json=pay)
    client.post(f"{base}/entries", json=entry_body(amount_cents=2000, category_id=food, rule=one_off("2026-03-10")))
    client.post(f"{base}/entries", json=entry_body(amount_cents=500, rule=one_off("2026-04-10")))

    board = client.get(f"{base}/dashboard", params={"start": "2026-03-01", "end": "2026-03-31"}).json()

    assert (board["income_cents"], board["expense_cents"]) == (5000, 2000)
    assert board["donut"] == {
        "total_cents": 5000,
        "slices": [{"category_id": food, "name": "Food", "amount_cents": 2000}],
        "remaining_cents": 3000,
        "mark_cents": None,
    }
    assert board["lines"]["unit"] == "day"
    assert board["lines"]["points"][-1] == {"date": "2026-03-31", "income_cum": 5000, "expense_cum": 2000}
    assert board["limits"] == []


def test_dashboard_last_n_units_and_bad_period(client, base):
    today = dt.date.today()
    board = client.get(f"{base}/dashboard", params={"last": 1, "unit": "week"}).json()
    assert board["range"]["end"] == today.isoformat()
    assert client.get(f"{base}/dashboard").status_code == 422
    assert client.get(f"{base}/dashboard", params={"start": "2026-03-02", "end": "2026-03-01"}).status_code == 422


def test_every_budget_route_depends_on_the_guard(app):
    routes = {(r.path, m): r for r in api_routes(app) for m in r.methods}
    guarded = 0
    for path, methods in app.openapi()["paths"].items():
        if "{budget_id}" not in path:
            continue
        for method in methods:
            assert has_guard(routes[(path, method.upper())].dependant), f"{method} {path} is not guarded"
            guarded += 1
    assert guarded >= 10


def api_routes(app) -> list:
    return [r for inc in app.routes if hasattr(inc, "original_router") for r in inc.original_router.routes]


def has_guard(dependant) -> bool:
    return any(getattr(d.call, "is_budget_guard", False) or has_guard(d) for d in dependant.dependencies)


def test_non_member_gets_404_and_viewer_gets_403_on_write(app, client, base, tmp_path):
    outsider = sign_up(app, "bob@example.test")
    assert outsider.get(f"{base}/entries").status_code == 404
    assert outsider.post(f"{base}/categories", json={"kind": "expense", "name": "X"}).status_code == 404

    viewer = sign_up(app, "carol@example.test")
    db = sqlite3.connect(tmp_path / "app.db")
    db.execute(
        "INSERT INTO memberships (budget_id, user_id, role) SELECT ?, id, 'viewer' FROM users WHERE email = ?",
        (int(base.rsplit("/", 1)[1]), "carol@example.test"),
    )
    db.commit()
    db.close()

    assert viewer.get(f"{base}/entries").status_code == 200
    assert viewer.post(f"{base}/entries", json=entry_body()).status_code == 403
    assert viewer.delete(f"{base}/categories/1").status_code == 403


def test_split_with_null_required_field_is_422(client, base):
    entry_id = client.post(f"{base}/entries", json=entry_body()).json()["id"]
    resp = client.post(f"{base}/entries/{entry_id}/split", json={"at": "2026-06-01", "changes": {"amount_cents": None}})
    assert resp.status_code == 422


def test_put_one_off_with_recurring_rule_is_422_and_leaves_entry(client, base):
    created = client.post(f"{base}/entries", json=entry_body(rule=one_off("2026-03-01"))).json()
    assert client.put(f"{base}/entries/{created['id']}", json=entry_body()).status_code == 422
    assert client.get(f"{base}/entries").json() == [created]
