"""Sharing: shared budgets and invites."""

import sqlite3

from budget_app.domain.access import BudgetAccess
from budget_app.domain.accounts import normalise_email
from budget_app.repos import budgets, categories, invites, members, users
from budget_app.repos.budgets import BudgetSummary
from budget_app.repos.invites import Invite
from budget_app.repos.users import UserId


class InvalidEmail(ValueError):
    """The email is not an address."""


class PersonalBudget(Exception):
    """A personal budget can't be shared."""


class AlreadyInvitedOrMember(Exception):
    """The email is already a member or has a pending invite."""


class InviteNotFound(Exception):
    """No such pending invite for this caller."""


class NotYourInvite(Exception):
    """A viewer can revoke only the invites they sent."""


def create_shared(conn: sqlite3.Connection, user_id: UserId, name: str) -> BudgetSummary:
    """Create a shared budget with `user_id` as its editor and the default categories, in one transaction."""
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        budget_id = budgets.insert(conn, name, "shared", user_id)
        members.add(conn, budget_id, user_id, "editor")
        categories.seed_defaults(conn, BudgetAccess(budget_id, user_id, "editor", False))
    return BudgetSummary(budget_id, name, "shared", "editor")


def invite(conn: sqlite3.Connection, access: BudgetAccess, raw_email: str) -> Invite:
    """Invite the normalised email to the shared budget and return the pending invite.

    Raises InvalidEmail, PersonalBudget, or AlreadyInvitedOrMember for a member or a pending invite.
    """
    email = normalise_email(raw_email)
    if email is None:
        raise InvalidEmail
    if access.is_personal:
        raise PersonalBudget
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        if members.has_email(conn, access, email) or invites.has_pending(conn, access, email):
            raise AlreadyInvitedOrMember
        return invites.get(conn, invites.insert(conn, access, email))


def list_pending(conn: sqlite3.Connection, access: BudgetAccess) -> list[Invite]:
    """Return the budget's pending invites."""
    return invites.pending_in_budget(conn, access)


def revoke(conn: sqlite3.Connection, access: BudgetAccess, invite_id: int) -> None:
    """Delete a pending invite of the budget.

    Raises InviteNotFound when it is not a pending invite of this budget, and NotYourInvite when
    a viewer revokes an invite someone else sent.
    """
    found = invites.get(conn, invite_id)
    if found is None or found.budget_id != access.budget_id or found.status != "pending":
        raise InviteNotFound
    if access.role != "editor" and found.invited_by != access.user_id:
        raise NotYourInvite
    invites.delete(conn, invite_id)


def my_invites(conn: sqlite3.Connection, user_id: UserId) -> list[Invite]:
    """Return the pending invites addressed to the user's email."""
    user = users.by_id(conn, user_id)
    return invites.pending_for_email(conn, user.email)


def _addressed_to(conn: sqlite3.Connection, user_id: UserId, invite_id: int) -> Invite:
    found = invites.get(conn, invite_id)
    user = users.by_id(conn, user_id)
    if found is None or found.status != "pending" or found.email != user.email:
        raise InviteNotFound
    return found


def accept(conn: sqlite3.Connection, user_id: UserId, invite_id: int) -> BudgetSummary:
    """Make the addressee a viewer of the invite's budget and mark it accepted, in one transaction.

    Raises InviteNotFound unless the invite is pending and addressed to the user.
    """
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        found = _addressed_to(conn, user_id, invite_id)
        members.add(conn, found.budget_id, user_id, "viewer")
        invites.set_status(conn, invite_id, "accepted")
    return BudgetSummary(found.budget_id, found.budget_name, "shared", "viewer")


def decline(conn: sqlite3.Connection, user_id: UserId, invite_id: int) -> None:
    """Mark the invite declined.

    Raises InviteNotFound unless the invite is pending and addressed to the user.
    """
    conn.execute("BEGIN IMMEDIATE")
    with conn:
        _addressed_to(conn, user_id, invite_id)
        invites.set_status(conn, invite_id, "declined")
