from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category
from app.exceptions import NotFoundError, ConflictError


DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "color": "#FF6B6B"},
    {"name": "Transport", "color": "#4ECDC4"},
    {"name": "Housing", "color": "#45B7D1"},
    {"name": "Healthcare", "color": "#96CEB4"},
    {"name": "Entertainment", "color": "#FFEAA7"},
    {"name": "Shopping", "color": "#DDA0DD"},
    {"name": "Salary", "color": "#98FB98"},
    {"name": "Investment", "color": "#F0E68C"},
]


def seed_default_categories(db: Session) -> None:
    """Create default categories if they don't exist"""
    for cat_data in DEFAULT_CATEGORIES:
        existing = db.query(Category).filter(
            Category.name == cat_data["name"],
            Category.is_default == True
        ).first()
        if not existing:
            category = Category(
                name=cat_data["name"],
                color=cat_data["color"],
                is_default=True
            )
            db.add(category)
    db.commit()


def create_category(
    db: Session,
    user_id: int,
    name: str,
    color: str
) -> Category:
    existing = db.query(Category).filter(
        Category.user_id == user_id,
        Category.name == name,
        Category.is_active == True
    ).first()
    if existing:
        raise ConflictError(f"Category '{name}' already exists")

    category = Category(
        user_id=user_id,
        name=name,
        color=color,
        is_default=False
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_categories(db: Session, user_id: int) -> List[Category]:
    """Get all categories available to user (default + their own)"""
    return db.query(Category).filter(
        (Category.user_id == user_id) | (Category.is_default == True),
        Category.is_active == True
    ).all()


def get_category(db: Session, category_id: int, user_id: int) -> Category:
    category = db.query(Category).filter(
        Category.id == category_id,
        (Category.user_id == user_id) | (Category.is_default == True),
        Category.is_active == True
    ).first()
    if not category:
        raise NotFoundError("Category")
    return category


def update_category(
    db: Session,
    category_id: int,
    user_id: int,
    name: Optional[str],
    color: Optional[str]
) -> Category:
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id,
        Category.is_active == True
    ).first()
    if not category:
        raise NotFoundError("Category")

    if name is not None:
        category.name = name
    if color is not None:
        category.color = color

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int, user_id: int) -> None:
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id,
        Category.is_active == True
    ).first()
    if not category:
        raise NotFoundError("Category")

    category.is_active = False
    db.commit()