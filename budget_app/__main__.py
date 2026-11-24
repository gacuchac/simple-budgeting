"""Run the app: `python -m budget_app`."""

import uvicorn

from budget_app.api.app import create_app
from budget_app.db.connection import default_db_path


def main() -> None:
    """Serve the app on 127.0.0.1:8000 using the default database."""
    uvicorn.run(create_app(default_db_path()), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
