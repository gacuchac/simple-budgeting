"""Invites to shared budgets."""

from fastapi import APIRouter, HTTPException, Response

from budget_app.api.deps import Conn, CurrentUser, ViewAccess
from budget_app.api.schemas import BudgetOut, InviteIn, InviteOut
from budget_app.repos.invites import Invite
from budget_app.services import sharing

budget_router = APIRouter(prefix="/api/budgets/{budget_id}/invites")
router = APIRouter(prefix="/api/invites")


def _out(found: Invite) -> InviteOut:
    return InviteOut(
        id=found.id,
        budget_id=found.budget_id,
        budget_name=found.budget_name,
        email=found.email,
        invited_by_email=found.invited_by_email,
        status=found.status,
    )


@budget_router.post("", status_code=201)
def invite(body: InviteIn, access: ViewAccess, conn: Conn) -> InviteOut:
    """Invite an email; 409 for a personal budget, a member or a pending invite, 422 for a bad email."""
    try:
        return _out(sharing.invite(conn, access, body.email))
    except sharing.InvalidEmail:
        raise HTTPException(422, "not an email address") from None
    except sharing.PersonalBudget:
        raise HTTPException(409, "a personal budget can't be shared") from None
    except sharing.AlreadyInvitedOrMember:
        raise HTTPException(409, "already a member or invited") from None


@budget_router.get("")
def list_invites(access: ViewAccess, conn: Conn) -> list[InviteOut]:
    """Return the budget's pending invites."""
    return [_out(i) for i in sharing.list_pending(conn, access)]


@budget_router.delete("/{invite_id}", status_code=204)
def revoke_invite(invite_id: int, access: ViewAccess, conn: Conn) -> Response:
    """Revoke a pending invite; 404 when it is not one of the budget's, 403 for a viewer's others' invites."""
    try:
        sharing.revoke(conn, access, invite_id)
    except sharing.InviteNotFound:
        raise HTTPException(404) from None
    except sharing.NotYourInvite:
        raise HTTPException(403) from None
    return Response(status_code=204)


@router.get("")
def my_invites(user_id: CurrentUser, conn: Conn) -> list[InviteOut]:
    """Return the pending invites addressed to the caller's email."""
    return [_out(i) for i in sharing.my_invites(conn, user_id)]


@router.post("/{invite_id}/accept")
def accept_invite(invite_id: int, user_id: CurrentUser, conn: Conn) -> BudgetOut:
    """Join the invite's budget as a viewer; 404 unless the invite is pending and addressed to the caller."""
    try:
        joined = sharing.accept(conn, user_id, invite_id)
    except sharing.InviteNotFound:
        raise HTTPException(404) from None
    return BudgetOut(id=joined.id, name=joined.name, kind=joined.kind, role=joined.role)


@router.post("/{invite_id}/decline", status_code=204)
def decline_invite(invite_id: int, user_id: CurrentUser, conn: Conn) -> Response:
    """Decline the invite; 404 unless it is pending and addressed to the caller."""
    try:
        sharing.decline(conn, user_id, invite_id)
    except sharing.InviteNotFound:
        raise HTTPException(404) from None
    return Response(status_code=204)
