from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate,
    TransactionResponse, TransactionListResponse
)
from app.services import transaction_service
from app.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import TransactionType

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.create_transaction(
        db,
        user_id=current_user.id,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        notes=transaction_data.notes,
        transaction_date=transaction_data.transaction_date
    )


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions, total = transaction_service.get_transactions(
        db,
        user_id=current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        transactions=transactions
    )


@router.get("/summary/monthly", )
def get_monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.get_monthly_summary(
        db, current_user.id, year, month
    )


@router.get("/summary/categories")
def get_category_breakdown(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.get_category_breakdown(
        db, current_user.id, start_date, end_date
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.get_transaction(
        db, transaction_id, current_user.id
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return transaction_service.update_transaction(
        db,
        transaction_id=transaction_id,
        user_id=current_user.id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        notes=transaction_data.notes,
        transaction_date=transaction_data.transaction_date
    )


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction_service.delete_transaction(
        db, transaction_id, current_user.id
    )