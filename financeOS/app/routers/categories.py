from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services import category_service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return category_service.create_category(
        db,
        user_id=current_user.id,
        name=category_data.name,
        color=category_data.color
    )


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return category_service.get_categories(db, current_user.id)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return category_service.update_category(
        db,
        category_id=category_id,
        user_id=current_user.id,
        name=category_data.name,
        color=category_data.color
    )


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service.delete_category(db, category_id, current_user.id)