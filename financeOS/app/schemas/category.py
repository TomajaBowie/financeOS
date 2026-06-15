from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoryCreate(BaseModel):
    name: str
    color: str = "#000000"


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True