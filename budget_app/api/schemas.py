"""Request and response bodies."""

from typing import Literal

from pydantic import BaseModel


class Credentials(BaseModel):
    """Email and password as typed by the user."""

    email: str
    password: str


class AccountOut(BaseModel):
    """The signed-in account."""

    id: int
    email: str


class BudgetOut(BaseModel):
    """One budget in the caller's list."""

    id: int
    name: str
    kind: Literal["personal", "shared"]
    role: Literal["editor", "viewer"]
