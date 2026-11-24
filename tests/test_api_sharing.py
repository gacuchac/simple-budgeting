"""Tests for shared budgets and invites over the HTTP API (US-12, US-13, US-18)."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from budget_app.api.app import create_app

GOOD = "abcdefg1!"


@pytest.fixture
def app(tmp_path: Path):
    return create_app(tmp_path / "app.db")


def sign_up(app, email: str) -> TestClient:
    client = TestClient(app)
    assert client.post("/api/signup", json={"email": email, "password": GOOD}).status_code == 201
    return client


@pytest.fixture
def alice(app) -> TestClient:
    return sign_up(app, "alice@example.test")


@pytest.fixture
def bob(app) -> TestClient:
    return sign_up(app, "bob@example.test")


def new_shared(client: TestClient, name: str = "Household") -> int:
    resp = client.post("/api/budgets", json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def invite(client: TestClient, budget_id: int, email: str):
    return client.post(f"/api/budgets/{budget_id}/invites", json={"email": email})


def my_invites(client: TestClient) -> list[dict]:
    resp = client.get("/api/invites")
    assert resp.status_code == 200
    return resp.json()


def invite_id_for(client: TestClient, budget_id: int) -> int:
    (found,) = [i for i in my_invites(client) if i["budget_id"] == budget_id]
    return found["id"]


def role_in(client: TestClient, budget_id: int) -> str | None:
    return next((b["role"] for b in client.get("/api/budgets").json() if b["id"] == budget_id), None)


def pending(client: TestClient, budget_id: int) -> list[dict]:
    resp = client.get(f"/api/budgets/{budget_id}/invites")
    assert resp.status_code == 200
    return resp.json()


def join_as_viewer(owner: TestClient, budget_id: int, guest: TestClient, email: str) -> None:
    assert invite(owner, budget_id, email).status_code == 201
    assert guest.post(f"/api/invites/{invite_id_for(guest, budget_id)}/accept").status_code == 200


def test_us12_create_shared_budget_returns_editor_and_lists_it(alice):
    resp = alice.post("/api/budgets", json={"name": "Household"})

    assert resp.status_code == 201
    body = resp.json()
    assert (body["name"], body["kind"], body["role"]) == ("Household", "shared", "editor")
    listed = alice.get("/api/budgets").json()
    assert {"id": body["id"], "name": "Household", "kind": "shared", "role": "editor"} in listed
    assert len(listed) == 2


def test_us12_new_shared_budget_has_its_own_default_categories(alice):
    personal = alice.get("/api/budgets").json()[0]["id"]
    shared = new_shared(alice)

    shared_cats = alice.get(f"/api/budgets/{shared}/categories").json()
    assert len(shared_cats) == 10
    assert alice.post(f"/api/budgets/{shared}/categories", json={"kind": "expense", "name": "Boat"}).status_code == 201
    assert len(alice.get(f"/api/budgets/{personal}/categories").json()) == 10
    personal_ids = {c["id"] for c in alice.get(f"/api/budgets/{personal}/categories").json()}
    assert personal_ids.isdisjoint(c["id"] for c in shared_cats)


def test_us12_creator_is_the_only_editor(alice, bob):
    shared = new_shared(alice)
    join_as_viewer(alice, shared, bob, "bob@example.test")

    entry = {
        "kind": "expense",
        "name": "Rent",
        "amount_cents": 1000,
        "category_id": None,
        "source": None,
        "rule": {"type": "one_off", "date": "2026-03-01"},
    }
    assert alice.post(f"/api/budgets/{shared}/entries", json=entry).status_code == 201
    assert bob.post(f"/api/budgets/{shared}/entries", json=entry).status_code == 403


def test_us12_blank_shared_budget_name_is_422(alice):
    assert alice.post("/api/budgets", json={"name": "   "}).status_code == 422
    assert len(alice.get("/api/budgets").json()) == 1


def test_us13_invite_returns_201_pending_with_normalised_email(alice):
    shared = new_shared(alice)

    resp = invite(alice, shared, "  Bob@Example.TEST ")

    assert resp.status_code == 201
    assert resp.json()["email"] == "bob@example.test"
    assert resp.json()["status"] == "pending"


def test_us13_list_shows_pending_invites_with_sender(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "carol@example.test")
    join_as_viewer(alice, shared, bob, "bob@example.test")
    invite(bob, shared, "dave@example.test")

    listed = pending(alice, shared)

    assert {(i["email"], i["invited_by_email"]) for i in listed} == {
        ("carol@example.test", "alice@example.test"),
        ("dave@example.test", "bob@example.test"),
    }
    assert all(i["status"] == "pending" for i in listed)
    assert pending(bob, shared) == listed


def test_us13_viewer_can_invite(alice, bob):
    shared = new_shared(alice)
    join_as_viewer(alice, shared, bob, "bob@example.test")

    assert invite(bob, shared, "carol@example.test").status_code == 201


def test_us13_inviting_to_a_personal_budget_is_409(alice):
    personal = alice.get("/api/budgets").json()[0]["id"]

    assert invite(alice, personal, "bob@example.test").status_code == 409
    assert alice.get(f"/api/budgets/{personal}/invites").json() == []


def test_us13_duplicate_pending_invite_is_409_in_any_email_case(alice):
    shared = new_shared(alice)
    assert invite(alice, shared, "bob@example.test").status_code == 201

    assert invite(alice, shared, "BOB@example.test ").status_code == 409
    assert len(pending(alice, shared)) == 1


def test_us13_inviting_an_existing_member_is_409(alice, bob):
    shared = new_shared(alice)
    join_as_viewer(alice, shared, bob, "bob@example.test")

    assert invite(alice, shared, "bob@example.test").status_code == 409
    assert invite(bob, shared, "alice@example.test").status_code == 409


def test_us13_same_email_can_be_pending_in_two_budgets(alice):
    first = new_shared(alice, "One")
    second = new_shared(alice, "Two")

    assert invite(alice, first, "bob@example.test").status_code == 201
    assert invite(alice, second, "bob@example.test").status_code == 201


def test_us13_non_member_gets_404_on_the_budget_invite_routes(app, alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "carol@example.test")
    invite_id = pending(alice, shared)[0]["id"]

    assert invite(bob, shared, "dave@example.test").status_code == 404
    assert bob.get(f"/api/budgets/{shared}/invites").status_code == 404
    assert bob.delete(f"/api/budgets/{shared}/invites/{invite_id}").status_code == 404
    assert len(pending(alice, shared)) == 1


def test_us13_creator_revokes_any_pending_invite(alice, bob):
    shared = new_shared(alice)
    join_as_viewer(alice, shared, bob, "bob@example.test")
    invite(bob, shared, "carol@example.test")
    invite(alice, shared, "dave@example.test")

    for item in pending(alice, shared):
        assert alice.delete(f"/api/budgets/{shared}/invites/{item['id']}").status_code == 204

    assert pending(alice, shared) == []


def test_us13_viewer_revokes_only_their_own_invites(alice, bob):
    shared = new_shared(alice)
    join_as_viewer(alice, shared, bob, "bob@example.test")
    invite(bob, shared, "carol@example.test")
    invite(alice, shared, "dave@example.test")
    by_email = {i["email"]: i["id"] for i in pending(alice, shared)}

    assert bob.delete(f"/api/budgets/{shared}/invites/{by_email['dave@example.test']}").status_code == 403
    assert bob.delete(f"/api/budgets/{shared}/invites/{by_email['carol@example.test']}").status_code == 204
    assert [i["email"] for i in pending(alice, shared)] == ["dave@example.test"]


def test_us13_revoke_of_an_unknown_or_other_budgets_invite_is_404(alice):
    first = new_shared(alice, "One")
    second = new_shared(alice, "Two")
    invite(alice, first, "bob@example.test")
    other = pending(alice, first)[0]["id"]

    assert alice.delete(f"/api/budgets/{second}/invites/{other}").status_code == 404
    assert alice.delete(f"/api/budgets/{first}/invites/99999").status_code == 404
    assert len(pending(alice, first)) == 1


def test_us13_revoked_invite_disappears_for_the_invitee_and_can_be_sent_again(app, alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    invite_id = invite_id_for(bob, shared)

    assert alice.delete(f"/api/budgets/{shared}/invites/{invite_id}").status_code == 204

    assert my_invites(bob) == []
    assert invite(alice, shared, "bob@example.test").status_code == 201
    assert len(my_invites(bob)) == 1


def test_us18_invite_made_before_signup_appears_normalised_after_signup(app, alice):
    shared = new_shared(alice)
    assert invite(alice, shared, "ALICE2@Example.Test").status_code == 201

    late = sign_up(app, " Alice2@example.TEST ")

    listed = my_invites(late)
    assert len(listed) == 1
    assert (listed[0]["budget_id"], listed[0]["budget_name"]) == (shared, "Household")
    assert listed[0]["email"] == "alice2@example.test"
    assert listed[0]["invited_by_email"] == "alice@example.test"


def test_us18_my_invites_lists_only_my_pending_ones(alice, bob):
    first = new_shared(alice, "One")
    second = new_shared(alice, "Two")
    invite(alice, first, "bob@example.test")
    invite(alice, second, "carol@example.test")
    invite(alice, second, "bob@example.test")
    declined = invite_id_for(bob, first)
    assert bob.post(f"/api/invites/{declined}/decline").status_code == 204

    assert [i["budget_id"] for i in my_invites(bob)] == [second]
    assert my_invites(alice) == []


def test_us18_accept_makes_the_user_a_viewer(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    assert role_in(bob, shared) is None

    resp = bob.post(f"/api/invites/{invite_id_for(bob, shared)}/accept")

    assert resp.status_code == 200
    assert role_in(bob, shared) == "viewer"
    assert my_invites(bob) == []
    assert bob.get(f"/api/budgets/{shared}/entries").status_code == 200
    assert bob.post(f"/api/budgets/{shared}/categories", json={"kind": "expense", "name": "X"}).status_code == 403
    assert pending(alice, shared) == []


def test_us18_decline_removes_the_invite_and_adds_no_membership(app, tmp_path, alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    invite_id = invite_id_for(bob, shared)

    assert bob.post(f"/api/invites/{invite_id}/decline").status_code == 204

    assert my_invites(bob) == []
    assert role_in(bob, shared) is None
    assert bob.get(f"/api/budgets/{shared}/entries").status_code == 404
    db = sqlite3.connect(tmp_path / "app.db")
    try:
        assert db.execute("SELECT status FROM invites WHERE id = ?", (invite_id,)).fetchall() == [("declined",)]
    finally:
        db.close()


def test_us18_declined_invitee_can_be_invited_again(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    bob.post(f"/api/invites/{invite_id_for(bob, shared)}/decline")

    assert invite(alice, shared, "bob@example.test").status_code == 201

    assert bob.post(f"/api/invites/{invite_id_for(bob, shared)}/accept").status_code == 200
    assert role_in(bob, shared) == "viewer"


@pytest.mark.parametrize("action", ["accept", "decline"])
def test_us18_only_the_addressee_can_act_on_an_invite(app, alice, bob, action):
    shared = new_shared(alice)
    invite(alice, shared, "carol@example.test")
    carol = sign_up(app, "carol@example.test")
    invite_id = invite_id_for(carol, shared)

    assert bob.post(f"/api/invites/{invite_id}/{action}").status_code == 404
    assert alice.post(f"/api/invites/{invite_id}/{action}").status_code == 404
    assert role_in(bob, shared) is None
    assert len(my_invites(carol)) == 1


def test_us18_accepting_a_revoked_invite_fails_and_adds_no_membership(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    invite_id = invite_id_for(bob, shared)
    alice.delete(f"/api/budgets/{shared}/invites/{invite_id}")

    assert bob.post(f"/api/invites/{invite_id}/accept").status_code in (404, 409)
    assert role_in(bob, shared) is None


def test_us18_accepting_twice_fails(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    invite_id = invite_id_for(bob, shared)
    assert bob.post(f"/api/invites/{invite_id}/accept").status_code == 200

    assert bob.post(f"/api/invites/{invite_id}/accept").status_code in (404, 409)
    assert role_in(bob, shared) == "viewer"


def test_us18_declined_invite_cannot_then_be_accepted(alice, bob):
    shared = new_shared(alice)
    invite(alice, shared, "bob@example.test")
    invite_id = invite_id_for(bob, shared)
    bob.post(f"/api/invites/{invite_id}/decline")

    assert bob.post(f"/api/invites/{invite_id}/accept").status_code in (404, 409)
    assert role_in(bob, shared) is None


def test_us18_membership_in_one_budget_does_not_block_an_invite_to_another(alice, bob):
    first = new_shared(alice, "One")
    second = new_shared(alice, "Two")
    join_as_viewer(alice, first, bob, "bob@example.test")

    assert invite(alice, second, "bob@example.test").status_code == 201
    assert role_in(bob, second) is None
