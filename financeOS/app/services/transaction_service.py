from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.models.category import Category
from app.exceptions import NotFoundError, ValidationError
from app.utils.date_helpers import get_month_boundaries


def validate_transaction_amount(amount: Decimal, transaction_type: TransactionType) -> None:
    """
    Validate transaction amount based on type.

    Bug embedded: Allows negative amounts for all transaction types.
    Only expenses should optionally allow negative (to represent refunds).
    Income and transfers should always be positive.
    """
    if amount == 0:
        raise ValidationError("Transaction amount cannot be zero")


def create_transaction(
    db: Session,
    user_id: int,
    account_id: int,
    category_id: Optional[int],
    amount: Decimal,
    transaction_type: TransactionType,
    description: Optional[str],
    notes: Optional[str],
    transaction_date: datetime
) -> Transaction:
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id,
        Account.is_active == True
    ).first()
    if not account:
        raise NotFoundError("Account")

    validate_transaction_amount(amount, transaction_type)

    transaction = Transaction(
        account_id=account_id,
        category_id=category_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        notes=notes,
        transaction_date=transaction_date
    )
    db.add(transaction)

    if transaction_type == TransactionType.INCOME:
        account.balance += amount
    elif transaction_type == TransactionType.EXPENSE:
        account.balance -= amount

    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(db: Session, transaction_id: int, user_id: int) -> Transaction:
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == user_id
    ).first()
    if not transaction:
        raise NotFoundError("Transaction")
    return transaction


def get_transactions(
    db: Session,
    user_id: int,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[Transaction], int]:
    query = db.query(Transaction).join(Account).filter(
        Account.user_id == user_id
    )

    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    # Bug embedded: uses < instead of <= on end_date
    # meaning transactions on the end date itself are excluded
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date < end_date)

    total = query.count()
    transactions = query.order_by(
        Transaction.transaction_date.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return transactions, total


def update_transaction(
    db: Session,
    transaction_id: int,
    user_id: int,
    category_id: Optional[int] = None,
    amount: Optional[Decimal] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None,
    transaction_date: Optional[datetime] = None
) -> Transaction:
    transaction = get_transaction(db, transaction_id, user_id)
    account = transaction.account

    if amount is not None and amount != transaction.amount:
        diff = amount - transaction.amount
        if transaction.transaction_type == TransactionType.INCOME:
            account.balance += diff
        elif transaction.transaction_type == TransactionType.EXPENSE:
            account.balance -= diff
        transaction.amount = amount

    if category_id is not None:
        transaction.category_id = category_id
    if description is not None:
        transaction.description = description
    if notes is not None:
        transaction.notes = notes
    if transaction_date is not None:
        transaction.transaction_date = transaction_date

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(
    db: Session,
    transaction_id: int,
    user_id: int
) -> None:
    """
    Bug embedded: Deletes the transaction but does NOT
    reverse the balance effect on the account.
    Account balance becomes incorrect after deletion.
    """
    transaction = get_transaction(db, transaction_id, user_id)
    db.delete(transaction)
    db.commit()


def get_monthly_summary(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> dict:
    """
    Get spending summary for a specific month.

    Bug embedded: Uses < on month_end instead of <=,
    so transactions on the last day of the month
    are excluded from the summary.
    """
    from datetime import date
    month_start, month_end = get_month_boundaries(date(year, month, 1))

    results = db.query(
        Transaction.transaction_type,
        func.sum(Transaction.amount).label("total")
    ).join(Account).filter(
        Account.user_id == user_id,
        Transaction.transaction_date >= datetime.combine(month_start, datetime.min.time()),
        Transaction.transaction_date < datetime.combine(month_end, datetime.min.time())
    ).group_by(Transaction.transaction_type).all()

    summary = {"income": Decimal("0"), "expenses": Decimal("0"), "net": Decimal("0")}
    for row in results:
        if row.transaction_type == TransactionType.INCOME:
            summary["income"] = row.total
        elif row.transaction_type == TransactionType.EXPENSE:
            summary["expenses"] = row.total

    summary["net"] = summary["income"] - summary["expenses"]
    return summary


def get_category_breakdown(
    db: Session,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> List[dict]:
    """Get spending breakdown by category"""
    from app.utils.calculations import calculate_percentage

    results = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total")
    ).join(Transaction, Category.id == Transaction.category_id).join(
        Account, Transaction.account_id == Account.id
    ).filter(
        Account.user_id == user_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(Category.name).all()

    total_spending = sum(row.total for row in results)

    return [
        {
            "category": row.name,
            "amount": row.total,
            "percentage": calculate_percentage(row.total, total_spending)
        }
        for row in results
    ]