from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database import get_database_session
from app.models.user import User
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentResponse,
    EnvironmentUpdate,
)
from app.services.environment_service import (
    create_environment,
    delete_environment,
    get_environment,
    list_project_environments,
    update_environment,
)


router = APIRouter(
    tags=["Environments"],
)


@router.post(
    "/projects/{project_id}/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_environment(
    project_id: UUID,
    environment_data: EnvironmentCreate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> EnvironmentResponse:
    try:
        return create_environment(
            database=database,
            project_id=project_id,
            owner_id=current_user.id,
            environment_data=environment_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bu proje içerisinde aynı isimde "
                "bir environment zaten bulunuyor."
            ),
        ) from error


@router.get(
    "/projects/{project_id}/environments",
    response_model=list[EnvironmentResponse],
)
def list_environments(
    project_id: UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> list[EnvironmentResponse]:
    return list_project_environments(
        database=database,
        project_id=project_id,
        owner_id=current_user.id,
    )


@router.get(
    "/environments/{environment_id}",
    response_model=EnvironmentResponse,
)
def read_environment(
    environment_id: UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> EnvironmentResponse:
    environment = get_environment(
        database=database,
        environment_id=environment_id,
        owner_id=current_user.id,
    )

    if environment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment bulunamadı.",
        )

    return environment


@router.put(
    "/environments/{environment_id}",
    response_model=EnvironmentResponse,
)
def update_existing_environment(
    environment_id: UUID,
    environment_data: EnvironmentUpdate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> EnvironmentResponse:
    environment = get_environment(
        database=database,
        environment_id=environment_id,
        owner_id=current_user.id,
    )

    if environment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment bulunamadı.",
        )

    try:
        return update_environment(
            database=database,
            environment=environment,
            update_data=environment_data,
        )

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bu proje içerisinde aynı isimde "
                "bir environment zaten bulunuyor."
            ),
        ) from error


@router.delete(
    "/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_environment(
    environment_id: UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Response:
    environment = get_environment(
        database=database,
        environment_id=environment_id,
        owner_id=current_user.id,
    )

    if environment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment bulunamadı.",
        )

    delete_environment(
        database=database,
        environment=environment,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )