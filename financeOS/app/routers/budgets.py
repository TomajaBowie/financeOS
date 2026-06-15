from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetStatusResponse
from app.services import budget_service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.post("", response_model=BudgetResponse, status_code=201)
def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return budget_service.create_budget(
        db,
        user_id=current_user.id,
        category_id=budget_data.category_id,
        amount_limit=budget_data.amount_limit,
        period_start=budget_data.period_start,
        period_end=budget_data.period_end
    )


@router.get("", response_model=List[BudgetResponse])
def get_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return budget_service.get_active_budgets(db, current_user.id)


@router.get("/{budget_id}/status", response_model=BudgetStatusResponse)
def get_budget_status(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return budget_service.get_budget_status(db, budget_id, current_user.id)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return budget_service.update_budget(
        db,
        budget_id=budget_id,
        user_id=current_user.id,
        amount_limit=budget_data.amount_limit,
        period_end=budget_data.period_end
    )


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget_service.delete_budget(db, budget_id, current_user.id)