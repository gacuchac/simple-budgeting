"""The caller's access to one budget."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class BudgetAccess:
    """A user's role in one budget, as resolved by the access guard."""

    budget_id: int
    user_id: int
    role: Literal["editor", "viewer"]
    is_personal: bool
