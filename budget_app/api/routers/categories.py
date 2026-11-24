"""Categories of a budget."""

from fastapi import APIRouter, HTTPException, Response

from budget_app.api.deps import Conn, EditAccess, ViewAccess
from budget_app.api.schemas import CategoryIn, CategoryOut, CategoryRename
from budget_app.repos.categories import Category
from budget_app.services import categories

router = APIRouter(prefix="/api/budgets/{budget_id}/categories")


def _out(category: Category) -> CategoryOut:
    return CategoryOut(id=category.id, budget_id=category.budget_id, kind=category.kind, name=category.name)


@router.get("")
def list_categories(access: ViewAccess, conn: Conn) -> list[CategoryOut]:
    """Return the budget's categories."""
    return [_out(c) for c in categories.list_all(conn, access)]


@router.post("", status_code=201)
def add_category(body: CategoryIn, access: EditAccess, conn: Conn) -> CategoryOut:
    """Add a category; 409 when the name exists for the kind."""
    try:
        return _out(categories.add(conn, access, body.kind, body.name))
    except categories.NameTaken:
        raise HTTPException(409, "category name already exists") from None


@router.put("/{category_id}")
def rename_category(category_id: int, body: CategoryRename, access: EditAccess, conn: Conn) -> CategoryOut:
    """Rename a category; 404 when it is not in the budget, 409 when the name exists for the kind."""
    try:
        return _out(categories.rename(conn, access, category_id, body.name))
    except categories.NameTaken:
        raise HTTPException(409, "category name already exists") from None
    except categories.CategoryNotFound:
        raise HTTPException(404) from None


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, access: EditAccess, conn: Conn) -> Response:
    """Delete a category; its entries become uncategorized; 404 when it is not in the budget."""
    try:
        categories.remove(conn, access, category_id)
    except categories.CategoryNotFound:
        raise HTTPException(404) from None
    return Response(status_code=204)
