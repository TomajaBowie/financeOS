from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from app.models.recurring import RecurringFrequency
from app.models.transaction import TransactionType


class RecurringCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    amount: Decimal
    transaction_type: TransactionType
    description: Optional[str] = None
    frequency: RecurringFrequency
    start_date: date
    end_date: Optional[date] = None


class RecurringResponse(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int]
    amount: Decimal
    transaction_type: TransactionType
    description: Optional[str]
    frequency: RecurringFrequency
    start_date: date
    next_due_date: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True