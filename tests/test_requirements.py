"""US-1: pinned Python requirements, pytest config and CI install."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RUNTIME = {
    "fastapi": "0.165.0",
    "pydantic": "2.14.4",
    "uvicorn": "0.54.0",
    "pwdlib[argon2]": "0.4.2",
    "argon2-cffi": "25.1.0",
}
DEV = {"pytest": "9.2.0", "httpx": "0.28.1"}

PIN = re.compile(r"^([A-Za-z0-9_.\-]+(?:\[[A-Za-z0-9_,\-]+\])?)==([^\s;#]+)$")


def _pins(name: str) -> dict[str, str]:
    path = ROOT / name
    assert path.is_file(), f"{name} is missing"
    pins = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.match(line)
        assert match, f"{name}: line is not pinned with ==: {line!r}"
        pins[match.group(1).lower()] = match.group(2)
    return pins


def test_us1_runtime_requirements_pin_exact_versions() -> None:
    assert _pins("requirements.txt") == RUNTIME


def test_us1_dev_requirements_pin_every_line_with_double_equals() -> None:
    _pins("requirements-dev.txt")


def test_us1_dev_requirements_pin_test_tools_and_ruff() -> None:
    pins = _pins("requirements-dev.txt")
    for package, version in DEV.items():
        assert pins.get(package) == version
    assert "ruff" in pins


def test_us1_ci_installs_runtime_and_dev_requirements() -> None:
    workflow = (ROOT / ".github/workflows/tests.yml").read_text()
    installs = [ln for ln in workflow.splitlines() if "pip install" in ln]
    assert any(
        "-r requirements.txt" in ln and "-r requirements-dev.txt" in ln
        for ln in installs
    ), installs


def test_us1_pytest_collects_only_tests_folder() -> None:
    path = ROOT / "pytest.ini"
    assert path.is_file(), "pytest.ini is missing"
    text = path.read_text()
    assert re.search(r"^\s*testpaths\s*=\s*tests\s*$", text, re.MULTILINE)
