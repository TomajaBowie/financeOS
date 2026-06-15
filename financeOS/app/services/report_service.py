from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account, AccountType
from app.models.category import Category
from app.utils.calculations import calculate_trend, calculate_net_worth
from app.utils.date_helpers import (
    get_month_boundaries,
    get_week_boundaries,
    get_previous_period
)


def get_spending_trend(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> dict:
    """Compare spending in current period vs previous period"""
    prev_start, prev_end = get_previous_period(start_date, end_date)

    current_spending = db.query(func.sum(Transaction.amount)).join(Account).filter(
        Account.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= datetime.combine(start_date, datetime.min.time()),
        Transaction.transaction_date <= datetime.combine(end_date, datetime.max.time())
    ).scalar() or Decimal("0")

    previous_spending = db.query(func.sum(Transaction.amount)).join(Account).filter(
        Account.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= datetime.combine(prev_start, datetime.min.time()),
        Transaction.transaction_date <= datetime.combine(prev_end, datetime.max.time())
    ).scalar() or Decimal("0")

    change = calculate_trend(current_spending, previous_spending)

    return {
        "current_period_spending": current_spending,
        "previous_period_spending": previous_spending,
        "change_percentage": change,
        "trend_direction": "up" if change > 0 else "down"
    }


def get_net_worth(db: Session, user_id: int) -> dict:
    """
    Calculate user net worth across all accounts.
    Uses calculate_net_worth which has the liability exclusion bug.
    """
    accounts = db.query(Account).filter(
        Account.user_id == user_id,
        Account.is_active == True
    ).all()

    account_balances = {str(a.id): a.balance for a in accounts}
    account_types = {str(a.id): a.account_type.value for a in accounts}

    net_worth = calculate_net_worth(account_balances, account_types)

    assets = sum(
        a.balance for a in accounts
        if a.account_type not in (AccountType.LIABILITY, AccountType.LOAN)
    )
    liabilities = sum(
        a.balance for a in accounts
        if a.account_type in (AccountType.LIABILITY, AccountType.LOAN)
    )

    return {
        "total_assets": assets,
        "total_liabilities": liabilities,
        "net_worth": net_worth,
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.account_type.value,
                "balance": a.balance
            }
            for a in accounts
        ]
    }


def get_weekly_report(
    db: Session,
    user_id: int,
    reference_date: date
) -> dict:
    """Get income/expense summary for the week containing reference_date"""
    week_start, week_end = get_week_boundaries(reference_date)

    results = db.query(
        Transaction.transaction_type,
        func.sum(Transaction.amount).label("total")
    ).join(Account).filter(
        Account.user_id == user_id,
        Transaction.transaction_date >= datetime.combine(week_start, datetime.min.time()),
        Transaction.transaction_date <= datetime.combine(week_end, datetime.max.time())
    ).group_by(Transaction.transaction_type).all()

    income = Decimal("0")
    expenses = Decimal("0")
    for row in results:
        if row.transaction_type == TransactionType.INCOME:
            income = row.total
        elif row.transaction_type == TransactionType.EXPENSE:
            expenses = row.total

    top_category = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total")
    ).join(Transaction, Category.id == Transaction.category_id).join(
        Account, Transaction.account_id == Account.id
    ).filter(
        Account.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= datetime.combine(week_start, datetime.min.time()),
        Transaction.transaction_date <= datetime.combine(week_end, datetime.max.time())
    ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).first()

    return {
        "week_start": week_start,
        "week_end": week_end,
        "income": income,
        "expenses": expenses,
        "net": income - expenses,
        "top_category": top_category.name if top_category else None
    }


def get_monthly_trends(
    db: Session,
    user_id: int,
    months: int = 6
) -> List[dict]:
    """Get monthly income vs expense summary for the last N months"""
    today = date.today()
    results = []

    for i in range(months - 1, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        month_start, month_end = get_month_boundaries(date(year, month, 1))

        rows = db.query(
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).join(Account).filter(
            Account.user_id == user_id,
            Transaction.transaction_date >= datetime.combine(
                month_start, datetime.min.time()
            ),
            Transaction.transaction_date <= datetime.combine(
                month_end, datetime.max.time()
            )
        ).group_by(Transaction.transaction_type).all()

        income = Decimal("0")
        expenses = Decimal("0")
        count = 0
        for row in rows:
            if row.transaction_type == TransactionType.INCOME:
                income = row.total
            elif row.transaction_type == TransactionType.EXPENSE:
                expenses = row.total
            count += row.count

        results.append({
            "year": year,
            "month": month,
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "transaction_count": count
        })

    return results