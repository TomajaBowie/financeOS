from pydantic import BaseModel
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import date


class MonthlySummary(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    net: Decimal
    transaction_count: int


class CategoryBreakdown(BaseModel):
    category: str
    amount: Decimal
    percentage: Decimal
    transaction_count: int


class TrendReport(BaseModel):
    current_period_spending: Decimal
    previous_period_spending: Decimal
    change_percentage: Decimal
    trend_direction: str


class NetWorthReport(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    accounts: List[dict]


class WeeklyReport(BaseModel):
    week_start: date
    week_end: date
    income: Decimal
    expenses: Decimal
    net: Decimal
    top_category: Optional[str]