import uuid

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    pass


def create_user(
    database: Session,
    user_data: UserCreate,
) -> User:
    normalized_email = str(user_data.email).lower()
    normalized_username = user_data.username.strip().lower()

    existing_user = database.scalar(
        select(User).where(
            or_(
                User.email == normalized_email,
                User.username == normalized_username,
            )
        )
    )

    if existing_user is not None:
        raise UserAlreadyExistsError(
            "Bu kullanıcı adı veya e-posta zaten kullanılıyor."
        )

    user = User(
        username=normalized_username,
        email=normalized_email,
        password_hash=hash_password(user_data.password),
    )

    database.add(user)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()

        raise UserAlreadyExistsError(
            "Bu kullanıcı adı veya e-posta zaten kullanılıyor."
        ) from error

    database.refresh(user)

    return user

def get_user_by_email(
        database: Session,
        email: str,
) -> User | None:
    normalized_email = email.strip().lower()

    return database.scalar(
        select(User).where(
            User.email == normalized_email,
        )
    )


def get_user_by_id(
        database: Session,
        user_id: uuid.UUID,
) -> User| None:
    return database.get(User, user_id)


def authenticate_user(
        database: Session,
        email: str,
        password: str,
) -> User | None:
    user = get_user_by_email(
        database = database,
        email=email,
    )

    if user is None:
        return None
    
    if not verify_password(
        plain_password=password,
        password_hash = user.password_hash,
    ):
        return None
    
    if not user.is_active:
        return None
    
    return user