from decimal import Decimal
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.exceptions import NotFoundError, ConflictError
from app.utils.calculations import (
    calculate_budget_utilization,
    is_budget_exceeded
)


def create_budget(
    db: Session,
    user_id: int,
    category_id: int,
    amount_limit: Decimal,
    period_start: date,
    period_end: date
) -> Budget:
    # Deactivate any existing budget for this category in overlapping period
    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.is_active == True
    ).first()

    if existing:
        existing.is_active = False

    budget = Budget(
        user_id=user_id,
        category_id=category_id,
        amount_limit=amount_limit,
        period_start=period_start,
        period_end=period_end,
        is_active=True
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget(db: Session, budget_id: int, user_id: int) -> Budget:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    if not budget:
        raise NotFoundError("Budget")
    return budget


def get_active_budgets(db: Session, user_id: int) -> List[Budget]:
    """
    Bug embedded: Returns ALL budgets where is_active=True
    including ones whose period has already ended.
    Should filter by period_end >= today to only show
    currently relevant budgets.
    """
    return db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.is_active == True
    ).all()


def get_budget_status(
    db: Session,
    budget_id: int,
    user_id: int
) -> dict:
    budget = get_budget(db, budget_id, user_id)

    spent = db.query(func.sum(Transaction.amount)).join(Account).filter(
        Account.user_id == user_id,
        Transaction.category_id == budget.category_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= budget.period_start,
        Transaction.transaction_date <= budget.period_end
    ).scalar() or Decimal("0")

    remaining = budget.amount_limit - spent
    utilization = calculate_budget_utilization(spent, budget.amount_limit)
    exceeded = is_budget_exceeded(spent, budget.amount_limit)

    return {
        "budget": budget,
        "spent": spent,
        "remaining": remaining,
        "utilization_percentage": utilization,
        "is_exceeded": exceeded,
        "is_warning": utilization >= Decimal("80")
    }


def update_budget(
    db: Session,
    budget_id: int,
    user_id: int,
    amount_limit: Optional[Decimal],
    period_end: Optional[date]
) -> Budget:
    budget = get_budget(db, budget_id, user_id)

    if amount_limit is not None:
        budget.amount_limit = amount_limit
    if period_end is not None:
        budget.period_end = period_end

    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget_id: int, user_id: int) -> None:
    budget = get_budget(db, budget_id, user_id)
    budget.is_active = False
    db.commit()