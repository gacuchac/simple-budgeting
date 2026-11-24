"""The caller's budgets."""

from fastapi import APIRouter

from budget_app.api.deps import Conn, CurrentUser
from budget_app.api.schemas import BudgetOut
from budget_app.services import accounts

router = APIRouter(prefix="/api")


@router.get("/budgets")
def list_budgets(user_id: CurrentUser, conn: Conn) -> list[BudgetOut]:
    """Return the budgets the signed-in user belongs to."""
    return [BudgetOut(id=b.id, name=b.name, kind=b.kind, role=b.role) for b in accounts.budgets_for(conn, user_id)]
