from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import settings
from app.exceptions import UnauthorizedError, ConflictError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def register_user(db: Session, email: str, username: str, password: str) -> User:
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise ConflictError("Email already registered")

    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise ConflictError("Username already taken")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise UnauthorizedError("Invalid email or password")

    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    user.last_login = datetime.utcnow()
    db.commit()
    return user


def refresh_access_token(db: Session, refresh_token: str) -> str:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedError("User not found")

        return create_access_token(user_id)
    except Exception:
        raise UnauthorizedError("Invalid or expired refresh token")


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")

    user.password_hash = hash_password(new_password)
    db.commit()