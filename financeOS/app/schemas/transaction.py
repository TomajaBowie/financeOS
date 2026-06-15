from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    amount: Decimal
    transaction_type: TransactionType
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: datetime


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int]
    amount: Decimal
    transaction_type: TransactionType
    description: Optional[str]
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    transactions: list[TransactionResponse]


class DateRangeFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    account_id: Optional[int] = None