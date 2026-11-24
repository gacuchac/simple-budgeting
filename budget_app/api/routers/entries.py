"""Entries of a budget, including edit-from-a-date."""

from fastapi import APIRouter, HTTPException, Response

from budget_app.api.deps import Conn, EditAccess, ViewAccess
from budget_app.api.schemas import (
    EntryChanges,
    EntryIn,
    EntryOut,
    EveryRule,
    MonthlyOnDayRule,
    OneOffRule,
    RuleBody,
    SplitIn,
    SplitOut,
)
from budget_app.domain.recurrence import Every, MonthlyOnDay, OneOff, Rule
from budget_app.repos.entries import Draft, Entry
from budget_app.services import entries

router = APIRouter(prefix="/api/budgets/{budget_id}/entries")


def _rule(body: RuleBody) -> Rule:
    try:
        match body:
            case OneOffRule():
                return OneOff(body.date)
            case EveryRule():
                return Every(body.n, body.unit, body.start, body.end)
            case MonthlyOnDayRule():
                return MonthlyOnDay(body.day, body.start, body.end)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


def _rule_body(rule: Rule) -> RuleBody:
    match rule:
        case OneOff():
            return OneOffRule(type="one_off", date=rule.date)
        case Every():
            return EveryRule(type="every", n=rule.n, unit=rule.unit, start=rule.start, end=rule.end)
        case MonthlyOnDay():
            return MonthlyOnDayRule(type="monthly_on_day", day=rule.day, start=rule.start, end=rule.end)


def _out(entry: Entry) -> EntryOut:
    return EntryOut(
        id=entry.id,
        budget_id=entry.budget_id,
        kind=entry.kind,
        name=entry.name,
        amount_cents=entry.amount_cents,
        category_id=entry.category_id,
        source=entry.source,
        rule=_rule_body(entry.rule),
    )


def _draft(body: EntryIn) -> Draft:
    return Draft(body.kind, body.name, body.amount_cents, body.category_id, body.source, _rule(body.rule))


def _changes(changes: EntryChanges) -> dict[str, object]:
    sent = {name: getattr(changes, name) for name in changes.model_fields_set}
    if sent.get("rule") is not None:
        sent["rule"] = _rule(sent["rule"])
    else:
        sent.pop("rule", None)
    return sent


@router.get("")
def list_entries(access: ViewAccess, conn: Conn) -> list[EntryOut]:
    """Return the budget's entries."""
    return [_out(e) for e in entries.list_all(conn, access)]


@router.post("", status_code=201)
def create_entry(body: EntryIn, access: EditAccess, conn: Conn) -> EntryOut:
    """Create an entry; 422 for a bad amount, source, category or rule."""
    try:
        return _out(entries.create(conn, access, _draft(body)))
    except entries.InvalidEntry as error:
        raise HTTPException(422, str(error)) from None


@router.put("/{entry_id}")
def replace_one_off(entry_id: int, body: EntryIn, access: EditAccess, conn: Conn) -> EntryOut:
    """Replace a one-off entry; 404 when it is not in the budget, 422 for a recurring entry or a bad body."""
    try:
        return _out(entries.update_one_off(conn, access, entry_id, _draft(body)))
    except entries.EntryNotFound:
        raise HTTPException(404) from None
    except entries.InvalidEntry as error:
        raise HTTPException(422, str(error)) from None


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, access: EditAccess, conn: Conn) -> Response:
    """Delete an entry and its whole series; 404 when it is not in the budget."""
    try:
        entries.remove(conn, access, entry_id)
    except entries.EntryNotFound:
        raise HTTPException(404) from None
    return Response(status_code=204)


@router.post("/{entry_id}/split", status_code=201)
def split_entry(entry_id: int, body: SplitIn, access: EditAccess, conn: Conn) -> SplitOut:
    """Edit a recurring entry from `at`; 404 when it is not in the budget, 422 for a one-off or `at` after its end."""
    try:
        result = entries.split(conn, access, entry_id, body.at, _changes(body.changes))
    except entries.EntryNotFound:
        raise HTTPException(404) from None
    except entries.InvalidEntry as error:
        raise HTTPException(422, str(error)) from None
    previous = None if result.previous is None else _out(result.previous)
    return SplitOut(previous=previous, current=_out(result.current))
