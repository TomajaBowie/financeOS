from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.database import get_db
from app.schemas.recurring import RecurringCreate, RecurringResponse
from app.services import recurring_service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/recurring", tags=["Recurring Transactions"])


@router.post("", response_model=RecurringResponse, status_code=201)
def create_recurring(
    data: RecurringCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return recurring_service.create_recurring(
        db,
        user_id=current_user.id,
        account_id=data.account_id,
        category_id=data.category_id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        description=data.description,
        frequency=data.frequency,
        start_date=data.start_date,
        end_date=data.end_date
    )


@router.get("", response_model=List[RecurringResponse])
def get_recurring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return recurring_service.get_user_recurring(db, current_user.id)


@router.post("/generate")
def generate_transactions(
    as_of_date: date = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if as_of_date is None:
        as_of_date = date.today()
    generated = recurring_service.generate_due_transactions(
        db, current_user.id, as_of_date
    )
    return {"generated_count": len(generated)}


@router.delete("/{recurring_id}", status_code=204)
def cancel_recurring(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recurring_service.cancel_recurring(db, recurring_id, current_user.id)