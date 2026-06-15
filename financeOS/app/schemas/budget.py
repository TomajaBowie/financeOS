from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class BudgetCreate(BaseModel):
    category_id: int
    amount_limit: Decimal
    period_start: date
    period_end: date


class BudgetUpdate(BaseModel):
    amount_limit: Optional[Decimal] = None
    period_end: Optional[date] = None


class BudgetResponse(BaseModel):
    id: int
    category_id: int
    amount_limit: Decimal
    period_start: date
    period_end: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    budget: BudgetResponse
    spent: Decimal
    remaining: Decimal
    utilization_percentage: Decimal
    is_exceeded: bool
    is_warning: bool