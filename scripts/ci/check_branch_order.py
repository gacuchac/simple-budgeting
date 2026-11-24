#!/usr/bin/env python3
"""Fail a pull request whose source branch may not merge into its target branch.

Rules: main takes only uat; uat takes dev or hotfix/*; dev takes feature/*,
bugfix/* or hotfix/*. Other target branches are not checked.
Reads BASE_REF, HEAD_REF, HEAD_REPO and REPO from the environment.
"""

import os
import sys

# A rule ending in "/" is a prefix (and needs a name after it); any other rule is an exact name.
ALLOWED_SOURCES: dict[str, tuple[str, ...]] = {
    "main": ("uat",),
    "uat": ("dev", "hotfix/"),
    "dev": ("feature/", "bugfix/", "hotfix/"),
}


def matches(head: str, rule: str) -> bool:
    """Return True if the branch name head satisfies one rule."""
    if rule.endswith("/"):
        return head.startswith(rule) and len(head) > len(rule)
    return head == rule


def is_allowed(base: str, head: str, same_repo: bool) -> bool:
    """Return True if a PR from head into base follows the branch order.

    A target branch with no rule allows any source. A PR from a fork is never
    allowed into a ruled branch.
    """
    rules = ALLOWED_SOURCES.get(base)
    if rules is None:
        return True
    return same_repo and any(matches(head, rule) for rule in rules)


def main() -> int:
    """Check the PR described by the environment; return the process exit code."""
    base, head = os.environ["BASE_REF"], os.environ["HEAD_REF"]
    same_repo = os.environ.get("HEAD_REPO", "") == os.environ["REPO"]
    if is_allowed(base, head, same_repo):
        print(f"OK: {head} -> {base}")
        return 0
    if not same_repo:
        print(f"Blocked: {base} doesn't take PRs from forks.", file=sys.stderr)
        return 1
    allowed = ", ".join(rule + "*" if rule.endswith("/") else rule for rule in ALLOWED_SOURCES[base])
    print(f"Blocked: {base} only takes PRs from {allowed}, not {head}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
