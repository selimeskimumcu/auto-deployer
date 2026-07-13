import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database import get_database_session
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import (
    create_project,
    delete_project,
    get_project_by_id_and_owner,
    get_projects_by_owner,
    update_project,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

@router.post(
    "",
    response_model=ProjectResponse,
    status_code= status.HTTP_201_CREATED,
)
def create_new_project(
    project_data: ProjectCreate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return create_project(
        database=database,
        owner_id=current_user.id,
        project_data=project_data,
    )

@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects(
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return get_projects_by_owner(
        database=database,
        owner_id=current_user.id,
    )

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: uuid.UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    project = get_project_by_id_and_owner(
        databese=database,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje Bulunamadı.",
        )
    return project

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_existing_project(
    project_id: uuid.UUID,
    project_data: ProjectUpdate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    project = get_project_by_id_and_owner(
        databese=database,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje Bulunamadı.",
        )
    
    return update_project(
        database=database,
        project=project,
        project_data=project_data,
    )

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_project(
    project_id: uuid.UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Response:
    project = get_project_by_id_and_owner(
        databese=database,
        project_id=project_id,
        owner_id=current_user.id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı.",
        )
    
    delete_project(
        database=database,
        project=project,
    )

    return Response(
        status_code= status.HTTP_204_NO_CONTENT,
    )