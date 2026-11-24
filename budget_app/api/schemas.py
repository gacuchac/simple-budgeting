"""Request and response bodies."""

import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator


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

    @model_validator(mode="after")
    def _no_null_required_fields(self) -> "EntryChanges":
        for field in ("name", "amount_cents"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


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


class LimitIn(BaseModel):
    """Set the limit of an expense category."""

    category_id: int
    amount_cents: Cents
    period: Literal["day", "week", "month", "year"]


class LimitOut(LimitIn):
    """A limit as stored."""

    id: int
    budget_id: int


class LimitStatusOut(BaseModel):
    """What a limit allows over a range, what was spent, and whether it is over."""

    limit_id: int
    category_id: int
    allowed_cents: int
    spent_cents: int
    over: bool


class LimitCheckOut(BaseModel):
    """The status of the category's limit for the expense form, or None when it has no limit."""

    status: LimitStatusOut | None


class DashboardOut(BaseModel):
    """The dashboard of a budget for one range."""

    range: RangeOut
    income_cents: int
    expense_cents: int
    donut: DonutOut
    lines: LinesOut
    limits: list[LimitStatusOut]


class BudgetIn(BaseModel):
    """A new shared budget."""

    name: Name


class InviteIn(BaseModel):
    """The email to invite."""

    email: str


class InviteOut(BaseModel):
    """An invite with its budget and sender."""

    id: int
    budget_id: int
    budget_name: str
    email: str
    invited_by_email: str
    status: Literal["pending", "accepted", "declined"]
