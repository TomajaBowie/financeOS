from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal
from app.models.account import AccountType


class AccountCreate(BaseModel):
    name: str
    account_type: AccountType
    initial_balance: Decimal = Decimal("0.00")
    currency: str = "USD"


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: AccountType
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AccountSummary(BaseModel):
    total_accounts: int
    total_balance: Decimal
    accounts: list[AccountResponse]