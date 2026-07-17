import uuid
from typing import Annotated

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