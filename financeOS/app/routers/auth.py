from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse,
    TokenResponse, RefreshTokenRequest, ChangePasswordRequest
)
from app.services import auth_service
from app.dependencies import get_current_user
from app.models.user import User
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = auth_service.register_user(
        db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.login_user(db, credentials.email, credentials.password)
    return TokenResponse(
        access_token=auth_service.create_access_token(user.id),
        refresh_token=auth_service.create_refresh_token(user.id)
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    new_access_token = auth_service.refresh_access_token(db, request.refresh_token)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    auth_service.change_password(
        db,
        current_user,
        request.current_password,
        request.new_password
    )
    return {"message": "Password changed successfully"}