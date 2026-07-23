import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.services.deployment_service import (
    get_deployment_by_id_and_owner,
    get_deployment_step_by_name,
    mark_step_failed,
    mark_step_running,
    mark_step_succeeded,
)
from app.services.docker_build_service import create_image_tag
from app.services.docker_registry_service import (
    publish_docker_image,
)


PUSH_IMAGE_STEP_NAME = "PushDockerImage"


def push_deployment_image(
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
        raise ValueError(
            "Deployment bulunamadı."
        )

    step = get_deployment_step_by_name(
        database=database,
        deployment_id=deployment.id,
        step_name=PUSH_IMAGE_STEP_NAME,
    )

    if step is None:
        raise ValueError(
            f"{PUSH_IMAGE_STEP_NAME} deployment adımı bulunamadı."
        )

    local_image_tag = create_image_tag(
        deployment_id=deployment.id,
    )

    mark_step_running(
        database=database,
        deployment_id=deployment.id,
        step_name=PUSH_IMAGE_STEP_NAME,
    )

    try:
        result = publish_docker_image(
            local_image_tag=local_image_tag,
            registry=settings.ghcr_registry,
            namespace=settings.ghcr_namespace,
            username=settings.ghcr_username,
            token=settings.ghcr_token,
            deployment_id=deployment.id,
        )

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name=PUSH_IMAGE_STEP_NAME,
        )

        return {
            "deployment_id": deployment.id,
            "local_image_tag": result.local_image_tag,
            "registry_image_tag": result.registry_image_tag,
            "digest": result.digest,
            "status": "succeeded",
            "push_logs": result.push_logs,
        }

    except Exception as exception:
        database.rollback()

        mark_step_failed(
            database=database,
            deployment_id=deployment.id,
            step_name=PUSH_IMAGE_STEP_NAME,
            error_message=str(exception),
        )

        raise