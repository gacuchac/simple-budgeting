"""Write the API's OpenAPI document: `python -m budget_app.export_openapi <output.json>`."""

import json
import sys
import tempfile
from pathlib import Path

from budget_app.api.app import create_app


def export_openapi(output: Path) -> None:
    """Write the OpenAPI document of `create_app` on a throwaway database to `output`."""
    with tempfile.TemporaryDirectory() as tmp:
        document = create_app(Path(tmp) / "openapi.sqlite3").openapi()
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    export_openapi(Path(sys.argv[1]))
