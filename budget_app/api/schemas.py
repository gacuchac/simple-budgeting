"""Request and response bodies."""

import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


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


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Cents = Annotated[int, Field(gt=0, strict=True)]


class CategoryIn(BaseModel):
    """A new category."""

    kind: Literal["income", "expense"]
    name: Name


class CategoryRename(BaseModel):
    """The new name of a category."""

    name: Name


class CategoryOut(BaseModel):
    """One category of a budget."""

    id: int
    budget_id: int
    kind: Literal["income", "expense"]
    name: str


class OneOffRule(BaseModel):
    """A single date."""

    type: Literal["one_off"]
    date: dt.date


class EveryRule(BaseModel):
    """Every `n` days, weeks or months."""

    type: Literal["every"]
    n: int = Field(ge=1)
    unit: Literal["day", "week", "month"]
    start: dt.date
    end: dt.date | None = None


class MonthlyOnDayRule(BaseModel):
    """Every month on `day`."""

    type: Literal["monthly_on_day"]
    day: int = Field(ge=1, le=31)
    start: dt.date
    end: dt.date | None = None


RuleBody = Annotated[OneOffRule | EveryRule | MonthlyOnDayRule, Field(discriminator="type")]


class EntryIn(BaseModel):
    """The body to create an entry or to replace a one-off."""

    kind: Literal["income", "expense"]
    name: Name
    amount_cents: Cents
    category_id: int | None = None
    source: str | None = None
    rule: RuleBody


class EntryOut(EntryIn):
    """An entry as stored."""

    id: int
    budget_id: int


class EntryChanges(BaseModel):
    """Fields a split changes; fields left out stay as they are."""

    name: Name | None = None
    amount_cents: Cents | None = None
    category_id: int | None = None
    source: str | None = None
    rule: Annotated[EveryRule | MonthlyOnDayRule, Field(discriminator="type")] | None = None


class SplitIn(BaseModel):
    """Edit a recurring entry from the date `at`."""

    at: dt.date
    changes: EntryChanges


class SplitOut(BaseModel):
    """The old entry (None after an in-place update) and the entry that applies from `at`."""

    previous: EntryOut | None
    current: EntryOut


class RangeOut(BaseModel):
    """Inclusive date range."""

    start: dt.date
    end: dt.date


class SliceOut(BaseModel):
    """Expense total of one category."""

    category_id: int | None
    name: str
    amount_cents: int


class DonutOut(BaseModel):
    """The donut chart's numbers."""

    total_cents: int
    slices: list[SliceOut]
    remaining_cents: int
    mark_cents: int | None


class PointOut(BaseModel):
    """Cumulative income and expense at the end of a bucket."""

    date: dt.date
    income_cum: int
    expense_cum: int


class LinesOut(BaseModel):
    """The line chart's numbers."""

    unit: Literal["day", "week", "month"]
    points: list[PointOut]


class DashboardOut(BaseModel):
    """The dashboard of a budget for one range (limits arrive with the limits feature)."""

    range: RangeOut
    income_cents: int
    expense_cents: int
    donut: DonutOut
    lines: LinesOut
    limits: list[dict] = Field(default_factory=list)
