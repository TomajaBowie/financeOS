from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import get_db
from app.config import settings
from app.exceptions import UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid token")
    except JWTError:
        raise UnauthorizedError("Invalid token")

    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("User not found")
    return user