"""Account rules: email normalisation and password strength."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")
_DIGIT = re.compile(r"[0-9]")


def normalise_email(raw: str) -> str | None:
    """Return `raw` stripped and lower-cased, or None when it is not an email address."""
    email = raw.strip().lower()
    return email if _EMAIL.match(email) else None


def password_problems(pw: str) -> list[str]:
    """Return the broken password rules in fixed order; an empty list means acceptable."""
    problems = []
    if len(pw) < 8:
        problems.append("at least 8 characters")
    if not _DIGIT.search(pw):
        problems.append("at least 1 number")
    if not _SPECIAL.search(pw):
        problems.append("at least 1 special character")
    return problems
