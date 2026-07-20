from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.services.deployment_service import (
    get_deployment_by_id_and_owner,
    get_deployment_step_by_name,
    mark_step_failed,
    mark_step_running,
    mark_step_succeeded,
)
from app.services.dockerfile_generator import generate_dockerfile
from app.services.project_analyzer import analyze_project
from app.services.repository_service import get_workspace_path


def prepare_deployment_dockerfile(
        database: Session,
        deployment_id,
        owner_id,
):
    deployment: Deployment | None = get_deployment_by_id_and_owner(
        database=database,
        deployment_id=deployment_id,
        owner_id= owner_id,
    )

    if deployment is None:
        raise ValueError("Deployment bulunamadı.")
    
    step = get_deployment_step_by_name(
        database=database,
        deployment_id=deployment.id,
        step_name="PrepareDockerfile",
    )

    if step is None:
        raise ValueError(
            "PrepareDockerfile deployment adımı bulunamadı."
        )
    
    mark_step_running(
        database=database,
        deployment_id=deployment.id,
        step_name="PrepareDockerfile",
    )

    try:
        workspace_path = get_workspace_path(
            str(deployment.id)
        )

        analysis = analyze_project (
            workspace_path
        )

        result = generate_dockerfile(
            workspace_path=workspace_path,
            framework=analysis.framework,
            project_type=analysis.project_type,
        )

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="PrepareDockerfile",
        )

        return {
            "deployment_id": deployment.id,
            "dockerfile_path": result.dockerfile_path,
            "generated": result.generated,
            "framework": analysis.framework,
            "project_type": analysis.project_type,
        }
    
    except Exception as exception:
        mark_step_failed(
            database=database,
            deployment_id=deployment.id,
            step_name="PrepareDockerfile",
            error_message=str(exception),
        )

        raise