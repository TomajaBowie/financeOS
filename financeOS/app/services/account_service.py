from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.account import Account, AccountType
from app.models.transaction import Transaction, TransactionType
from app.exceptions import NotFoundError, ValidationError


def create_account(
    db: Session,
    user_id: int,
    name: str,
    account_type: AccountType,
    initial_balance: Decimal,
    currency: str
) -> Account:
    account = Account(
        user_id=user_id,
        name=name,
        account_type=account_type,
        balance=initial_balance,
        currency=currency
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_account(db: Session, account_id: int, user_id: int) -> Account:
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id,
        Account.is_active == True
    ).first()
    if not account:
        raise NotFoundError("Account")
    return account


def get_user_accounts(db: Session, user_id: int) -> List[Account]:
    return db.query(Account).filter(
        Account.user_id == user_id,
        Account.is_active == True
    ).all()


def update_account(
    db: Session,
    account_id: int,
    user_id: int,
    name: Optional[str],
    currency: Optional[str]
) -> Account:
    account = get_account(db, account_id, user_id)

    if name is not None:
        account.name = name
    if currency is not None:
        account.currency = currency

    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: int, user_id: int) -> None:
    account = get_account(db, account_id, user_id)
    account.is_active = False
    db.commit()


def recalculate_balance(db: Session, account_id: int, user_id: int) -> Account:
    """Recalculate account balance from all transactions"""
    account = get_account(db, account_id, user_id)

    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_type == TransactionType.INCOME
    ).scalar() or Decimal("0")

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_type == TransactionType.EXPENSE
    ).scalar() or Decimal("0")

    account.balance = income - expenses
    db.commit()
    db.refresh(account)
    return account


def transfer_between_accounts(
    db: Session,
    source_id: int,
    destination_id: int,
    amount: Decimal,
    user_id: int
) -> tuple[Account, Account]:
    """Transfer amount from source to destination account"""
    source = get_account(db, source_id, user_id)
    destination = get_account(db, destination_id, user_id)

    if amount <= 0:
        raise ValidationError("Transfer amount must be positive")

    # Bug embedded here: credits destination BEFORE debiting source
    # This means if debit fails, destination keeps the money
    destination.balance += amount
    source.balance -= amount

    db.commit()
    db.refresh(source)
    db.refresh(destination)
    return source, destination