import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_database_session
from app.models.user import User
from app.services.user_service import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database: Annotated[Session, Depends(get_database_session)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = uuid.UUID(subject)

    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user_by_id(
        database=database,
        user_id=user_id,
    )

    if user is None or not user.is_active:
        raise credentials_exception

    return user