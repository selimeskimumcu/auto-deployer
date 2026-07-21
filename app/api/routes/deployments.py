import uuid
from typing import Annotated
from uuid import UUID

from app.database import get_database_session
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database import get_database_session
from app.models.user import User
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentDetailResponse,
    DeploymentResponse,
    DeploymentStepResponse,
)
from app.services.deployment_service import (
    EnvironmentNotFoundError,
    create_deployment,
    get_deployment_by_id_and_owner,
    get_deployment_steps,
    list_deployments_by_owner,
)
from app.schemas.deployment import DeploymentPrepareResponse
from app.services.deployment_prepare_service import (
    DeploymentPrepareError,
    prepare_deployment,
)
from app.schemas.deployment import DockerfilePrepareResponse
from app.services.deployment_dockerfile_service import (
    prepare_deployment_dockerfile,
)
from app.schemas.deployment import DockerImageBuildResponse
from app.services.deployment_image_service import build_deployment_image


router = APIRouter(
    prefix="/deployments",
    tags=["Deployments"],
)


@router.post(
    "",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_deployment(
    deployment_data: DeploymentCreate,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> DeploymentResponse:
    try:
        return create_deployment(
            database=database,
            environment_id=deployment_data.environment_id,
            owner_id=current_user.id,
            started_by_user_id=current_user.id,
        )

    except EnvironmentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Deployment version numarası oluşturulurken "
                "çakışma meydana geldi."
            ),
        ) from error


@router.get(
    "",
    response_model=list[DeploymentResponse],
)
def list_deployments(
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> list[DeploymentResponse]:
    return list_deployments_by_owner(
        database=database,
        owner_id=current_user.id,
    )


@router.get(
    "/{deployment_id}",
    response_model=DeploymentDetailResponse,
)
def get_deployment_detail(
    deployment_id: uuid.UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> DeploymentDetailResponse:
    deployment = get_deployment_by_id_and_owner(
        database=database,
        deployment_id=deployment_id,
        owner_id=current_user.id,
    )

    if deployment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment bulunamadı.",
        )

    steps = get_deployment_steps(
        database=database,
        deployment_id=deployment.id,
    )

    deployment_data = DeploymentResponse.model_validate(
        deployment
    )

    return DeploymentDetailResponse(
        **deployment_data.model_dump(),
        steps=[
            DeploymentStepResponse.model_validate(step)
            for step in steps
        ],
    )
@router.post(
    "/{deployment_id}/prepare",
    response_model=DeploymentPrepareResponse,
)
def prepare_existing_deployment(
    deployment_id: uuid.UUID,
    database: Annotated[
        Session,
        Depends(get_database_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> DeploymentPrepareResponse:
    deployment = get_deployment_by_id_and_owner(
        database=database,
        deployment_id=deployment_id,
        owner_id=current_user.id
    )

    if deployment is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Deployment bulunamadı.",
        )
    
    if deployment.status not in {
        "queued",
        "dailed",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bu deployment mevcut durumu nedeniyle "
                "hazırlanamaz."
            ),
        )
    
    try:
        result = prepare_deployment(
            database=database,
            deployment=deployment,
        )

        return DeploymentPrepareResponse(**result)
    
    except DeploymentPrepareError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    
@router.post(
    "/{deployment_id}/dockerfile",
    response_model=DockerfilePrepareResponse,
)
def prepare_dockerfile(
    deployment_id: uuid.UUID,
    database: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return prepare_deployment_dockerfile(
            database=database,
            deployment_id=deployment_id,
            owner_id=current_user.id,
        )

    except ValueError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        )

    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dockerfile hazırlanamadı: {exception}",
        )
    
@router.post(
    "/{deployment_id}/image",
    response_model=DockerImageBuildResponse,
    status_code=status.HTTP_200_OK,
)
def build_image(
    deployment_id: uuid.UUID,
    database: Annotated[
    Session,
    Depends(get_database_session),
],
    current_user = Depends(get_current_user),
):
    try:
        return build_deployment_image(
            database=database,
            deployment_id=deployment_id,
            owner_id=current_user.id,
        )
    
    except ValueError as exception:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception
    
    except FileNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detal=str(exception),
        ) from exception
    
    except RuntimeError as exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exception),
        ) from exception