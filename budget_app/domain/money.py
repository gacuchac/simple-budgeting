"""Money formatting for integer cents."""

from __future__ import annotations


def format_usd(cents: int) -> str:
    """Format integer cents as USD, e.g. `$1,234.50` or `-$12.34`.

    Raises TypeError for a float or a bool.
    """
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError(f"cents must be an int, got {type(cents).__name__}")
    sign = "-" if cents < 0 else ""
    dollars, rest = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{rest:02d}"
