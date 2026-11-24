"""US-1: email normalisation and password rules."""

import importlib

import pytest


def _accounts():
    return importlib.import_module("budget_app.domain.accounts")


@pytest.mark.parametrize(
    "raw",
    [
        "alice@example.com",
        " Alice@Example.COM ",
        "alice@example.test",
        " Alice@Example.Test ",
        "bob@team.local",
        "carol@demo.localhost",
        "dave@example.org",
    ],
)
def test_us1_normalise_email_accepts_and_lowercases(raw):
    assert _accounts().normalise_email(raw) == raw.strip().lower()


@pytest.mark.parametrize(
    "raw", ["alice", "alice@", "@x.com", "a b@x.com", "alice@example"]
)
def test_us1_normalise_email_rejects_bad_forms(raw):
    assert _accounts().normalise_email(raw) is None


@pytest.mark.parametrize(
    ("pw", "want"),
    [
        ("abcdefg1!", []),
        ("abcdefgh", ["at least 1 number", "at least 1 special character"]),
        ("abcdefg1", ["at least 1 special character"]),
        ("ab1!", ["at least 8 characters"]),
        (
            "",
            [
                "at least 8 characters",
                "at least 1 number",
                "at least 1 special character",
            ],
        ),
    ],
)
def test_us1_password_problems_lists_broken_rules(pw, want):
    assert _accounts().password_problems(pw) == want
