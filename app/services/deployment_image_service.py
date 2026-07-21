import uuid

from sqlalchemy.orm import Session

from app.services.deployment_service import (
    get_deployment_by_id_and_owner,
    get_deployment_step_by_name,
    mark_step_failed,
    mark_step_running,
    mark_step_succeeded,
)
from app.services.docker_build_service import build_docker_image
from app.services.repository_service import get_workspace_path

BUILD_IMAGE_STEP_NAME = "BuildDockerImage"


def build_deployment_image(
        database: Session,
        deployment_id: uuid.UUID,
        owner_id: uuid.UUID,
) -> dict:
    deployment = get_deployment_by_id_and_owner(
        database=database,
        deployment_id=deployment_id,
        owner_id=owner_id,
    )

    if deployment is None:
        raise ValueError("Deployment bulunamadı.")
    
    step = get_deployment_step_by_name(
        database=database,
        deployment_id=deployment.id,
        step_name=BUILD_IMAGE_STEP_NAME,
    )

    if step is None:
        raise ValueError(
            f"{BUILD_IMAGE_STEP_NAME} deployment adımı bulunamadı."
        )
    
    mark_step_running(
        database=database,
        deployment_id=deployment.id,
        step_name=BUILD_IMAGE_STEP_NAME,
    )

    try:
        workspace_path = get_workspace_path(
            str(deployment.id)
        )

        result = build_docker_image(
            workspace_path=workspace_path,
            deployment_id=deployment.id,
        )

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name=BUILD_IMAGE_STEP_NAME,
        )

        return {
            "deployment_id": deployment.id,
            "image_tag" : result.image_tag,
            "image_id": result.image_id,
            "status": "succeeded",
            "build_logs": result.build_logs,
        }
    
    except Exception as exception:
        database.rollback()

        mark_step_failed(
            database=database,
            deployment_id=deployment.id,
            step_name=BUILD_IMAGE_STEP_NAME,
            error_message= str(exception),
        )

        raise
    