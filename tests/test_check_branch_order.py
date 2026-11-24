import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "check_branch_order.py"
_spec = importlib.util.spec_from_file_location("check_branch_order", _path)
cbo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cbo)


def test_main_takes_only_uat():
    assert cbo.is_allowed("main", "uat", True)
    assert not cbo.is_allowed("main", "dev", True)
    assert not cbo.is_allowed("main", "hotfix/x", True)


def test_uat_takes_dev_and_hotfixes():
    assert cbo.is_allowed("uat", "dev", True)
    assert cbo.is_allowed("uat", "hotfix/login", True)
    assert not cbo.is_allowed("uat", "feature/x", True)


def test_dev_takes_task_branches_only():
    for head in ("feature/a", "bugfix/b", "hotfix/c"):
        assert cbo.is_allowed("dev", head, True)
    for head in ("uat", "main", "feature/", "featurex", "my-branch"):
        assert not cbo.is_allowed("dev", head, True)


def test_forks_are_blocked_and_other_bases_are_open():
    assert not cbo.is_allowed("dev", "feature/a", False)
    assert cbo.is_allowed("feature/a", "anything", True)
