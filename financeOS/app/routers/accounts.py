from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.account import (
    AccountCreate, AccountUpdate,
    AccountResponse, AccountSummary
)
from app.services import account_service
from app.dependencies import get_current_user
from app.models.user import User
from decimal import Decimal

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.create_account(
        db,
        user_id=current_user.id,
        name=account_data.name,
        account_type=account_data.account_type,
        initial_balance=account_data.initial_balance,
        currency=account_data.currency
    )


@router.get("", response_model=AccountSummary)
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = account_service.get_user_accounts(db, current_user.id)
    total_balance = sum(a.balance for a in accounts)
    return AccountSummary(
        total_accounts=len(accounts),
        total_balance=total_balance,
        accounts=accounts
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.get_account(db, account_id, current_user.id)


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.update_account(
        db,
        account_id=account_id,
        user_id=current_user.id,
        name=account_data.name,
        currency=account_data.currency
    )


@router.delete("/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account_service.delete_account(db, account_id, current_user.id)


@router.post("/{account_id}/recalculate", response_model=AccountResponse)
def recalculate_balance(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return account_service.recalculate_balance(db, account_id, current_user.id)


@router.post("/transfer", status_code=200)
def transfer(
    source_id: int,
    destination_id: int,
    amount: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source, destination = account_service.transfer_between_accounts(
        db, source_id, destination_id, amount, current_user.id
    )
    return {
        "message": "Transfer successful",
        "source_balance": source.balance,
        "destination_balance": destination.balance
    }