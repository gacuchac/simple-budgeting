"""Regenerate web/src/api/schema.d.ts from the API, or check that the committed copy is current.

`python scripts/gen_schema.py` rewrites the file; `python scripts/gen_schema.py --check` exits 1 when it is stale.
"""

import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SCHEMA = WEB / "src" / "api" / "schema.d.ts"


def generate(tmp: Path) -> str:
    """Return the schema.d.ts text that the current API produces."""
    openapi = tmp / "openapi.json"
    generated = tmp / "schema.d.ts"
    subprocess.run([sys.executable, "-m", "budget_app.export_openapi", str(openapi)], cwd=ROOT, check=True)
    subprocess.run(["npx", "--no-install", "openapi-typescript", str(openapi), "-o", str(generated)], cwd=WEB, check=True)
    return generated.read_text()


def main(argv: list[str]) -> int:
    """Rewrite the committed schema, or with `--check` print a diff and return 1 when it is stale."""
    with tempfile.TemporaryDirectory() as tmp:
        fresh = generate(Path(tmp))
    if "--check" not in argv:
        SCHEMA.write_text(fresh)
        return 0
    current = SCHEMA.read_text() if SCHEMA.exists() else ""
    if current == fresh:
        return 0
    sys.stdout.writelines(difflib.unified_diff(current.splitlines(True), fresh.splitlines(True), "committed", "generated"))
    print("schema.d.ts is stale: run `python scripts/gen_schema.py` and commit the result", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
