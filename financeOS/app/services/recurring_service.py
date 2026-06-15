from decimal import Decimal
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.recurring import RecurringTransaction, RecurringFrequency
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.exceptions import NotFoundError
from app.utils.date_helpers import get_month_boundaries


def get_next_due_date(
    current_date: date,
    frequency: RecurringFrequency
) -> date:
    """
    Calculate the next due date based on frequency.

    Bug embedded: For monthly frequency, uses a fixed 30-day
    offset instead of proper month arithmetic. This causes
    drift — a transaction created on Jan 31 will next be
    due on Mar 2 (skipping February entirely) instead of
    Feb 28/29.
    """
    if frequency == RecurringFrequency.DAILY:
        return current_date + timedelta(days=1)
    elif frequency == RecurringFrequency.WEEKLY:
        return current_date + timedelta(weeks=1)
    elif frequency == RecurringFrequency.MONTHLY:
        return current_date + timedelta(days=30)
    elif frequency == RecurringFrequency.YEARLY:
        return date(current_date.year + 1, current_date.month, current_date.day)


def create_recurring(
    db: Session,
    user_id: int,
    account_id: int,
    category_id: Optional[int],
    amount: Decimal,
    transaction_type: TransactionType,
    description: Optional[str],
    frequency: RecurringFrequency,
    start_date: date,
    end_date: Optional[date]
) -> RecurringTransaction:
    next_due = get_next_due_date(start_date, frequency)

    recurring = RecurringTransaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        amount=amount,
        transaction_type=str(transaction_type.value),
        description=description,
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        next_due_date=next_due,
        is_active=True
    )
    db.add(recurring)
    db.commit()
    db.refresh(recurring)
    return recurring


def get_recurring(
    db: Session,
    recurring_id: int,
    user_id: int
) -> RecurringTransaction:
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id,
        RecurringTransaction.user_id == user_id,
        RecurringTransaction.is_active == True
    ).first()
    if not recurring:
        raise NotFoundError("Recurring transaction")
    return recurring


def get_user_recurring(
    db: Session,
    user_id: int
) -> List[RecurringTransaction]:
    return db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id,
        RecurringTransaction.is_active == True
    ).all()


def generate_due_transactions(
    db: Session,
    user_id: int,
    as_of_date: date
) -> List[Transaction]:
    """
    Generate transactions for all recurring items due on or before as_of_date.

    Bug embedded: Does not check if a transaction was already
    generated today before creating a new one. Calling this
    function twice on the same day creates duplicate transactions.
    Should check last_generated date before proceeding.
    """
    due_recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id,
        RecurringTransaction.is_active == True,
        RecurringTransaction.next_due_date <= as_of_date
    ).all()

    generated = []
    for recurring in due_recurring:
        account = db.query(Account).filter(
            Account.id == recurring.account_id
        ).first()

        transaction = Transaction(
            account_id=recurring.account_id,
            category_id=recurring.category_id,
            amount=recurring.amount,
            transaction_type=recurring.transaction_type,
            description=recurring.description or f"Recurring: {recurring.frequency}",
            transaction_date=recurring.next_due_date
        )
        db.add(transaction)

        if recurring.transaction_type == "income":
            account.balance += recurring.amount
        elif recurring.transaction_type == "expense":
            account.balance -= recurring.amount

        recurring.last_generated = as_of_date
        recurring.next_due_date = get_next_due_date(
            recurring.next_due_date, recurring.frequency
        )

        if recurring.end_date and recurring.next_due_date > recurring.end_date:
            recurring.is_active = False

        generated.append(transaction)

    db.commit()
    return generated


def cancel_recurring(
    db: Session,
    recurring_id: int,
    user_id: int
) -> None:
    recurring = get_recurring(db, recurring_id, user_id)
    recurring.is_active = False
    db.commit()