from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.security import create_access_token
from app.database import get_database_session
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.user_service import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
) -> User:
    try:
        return create_user(
            database=database,
            user_data=user_data,
        )

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
) -> TokenResponse:
    user = authenticate_user(
        database=database,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya parola hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    return current_user