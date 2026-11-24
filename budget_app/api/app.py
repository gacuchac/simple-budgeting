"""The FastAPI app factory."""

from pathlib import Path

from fastapi import FastAPI

from budget_app.api.routers import auth, budgets, categories, dashboard, entries
from budget_app.db.connection import connect
from budget_app.db.migrate import migrate


def create_app(db_path: Path) -> FastAPI:
    """Migrate the database at `db_path` and return the app serving it, one connection per request."""
    conn = connect(db_path)
    migrate(conn)
    conn.close()
    app = FastAPI()
    app.state.db_path = db_path
    app.include_router(auth.router)
    app.include_router(budgets.router)
    app.include_router(categories.router)
    app.include_router(entries.router)
    app.include_router(dashboard.router)
    return app
