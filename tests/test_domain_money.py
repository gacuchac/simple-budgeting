"""US-3: format_usd turns integer cents into a USD string."""

import importlib

import pytest


def _format_usd():
    return importlib.import_module("budget_app.domain.money").format_usd


@pytest.mark.parametrize(
    ("cents", "want"),
    [
        (0, "$0.00"),
        (5, "$0.05"),
        (123450, "$1,234.50"),
        (100000000, "$1,000,000.00"),
        (-1234, "-$12.34"),
    ],
)
def test_us3_format_usd_formats_cents(cents, want):
    assert _format_usd()(cents) == want


@pytest.mark.parametrize("bad", [12.5, True])
def test_us3_format_usd_rejects_float_and_bool(bad):
    fn = _format_usd()
    with pytest.raises(TypeError):
        fn(bad)
