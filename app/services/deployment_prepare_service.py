import uuid

from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.models.project import Project
from app.services.deployment_service import (
    mark_step_failed,
    mark_step_running,
    mark_step_succeeded,
)
from app.services.project_analyzer import analyze_project
from app.services.repository_service import (
    RepositoryError,
    clone_repository,
    get_commit_sha,
)


class DeploymentPrepareError(Exception):
    pass


def prepare_deployment(
    database: Session,
    deployment: Deployment,
) -> dict[str, object]:
    project = database.get(
        Project,
        deployment.project_id,
    )

    if project is None:
        raise DeploymentPrepareError(
            "Deployment projesi bulunamadı."
        )

    deployment.status = "cloning"
    database.commit()

    try:
        mark_step_running(
            database=database,
            deployment_id=deployment.id,
            step_name="ValidateRequest",
        )

        if not project.repository_url:
            raise DeploymentPrepareError(
                "Project repository URL bilgisi bulunmuyor."
            )

        if not project.branch:
            raise DeploymentPrepareError(
                "Project branch bilgisi bulunmuyor."
            )

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="ValidateRequest",
        )

        mark_step_running(
            database=database,
            deployment_id=deployment.id,
            step_name="CreateWorkspace",
        )

        # Workspace clone_repository içinde oluşturuluyor.
        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="CreateWorkspace",
        )

        mark_step_running(
            database=database,
            deployment_id=deployment.id,
            step_name="CloneRepository",
        )

        workspace = clone_repository(
            repository_url=project.repository_url,
            branch=deployment.branch,
            deployment_id=deployment.id,
        )

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="CloneRepository",
        )

        mark_step_running(
            database=database,
            deployment_id=deployment.id,
            step_name="ResolveCommit",
        )

        commit_sha = get_commit_sha(workspace)

        deployment.commit_sha = commit_sha
        database.commit()

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="ResolveCommit",
        )

        deployment.status = "analyzing"
        database.commit()

        mark_step_running(
            database=database,
            deployment_id=deployment.id,
            step_name="AnalyzeProject",
        )

        analysis = analyze_project(workspace)

        mark_step_succeeded(
            database=database,
            deployment_id=deployment.id,
            step_name="AnalyzeProject",
        )

        deployment.status = "queued"
        database.commit()
        database.refresh(deployment)

        return {
            "deployment_id": deployment.id,
            "status": deployment.status,
            "repository_url": project.repository_url,
            "branch": deployment.branch,
            "commit_sha": commit_sha,
            "workspace_path": str(workspace),
            "analysis": analysis.to_dict(),
        }

    except (RepositoryError, DeploymentPrepareError) as error:
        current_step = "CloneRepository"

        if deployment.commit_sha:
            current_step = "AnalyzeProject"

        mark_step_failed(
            database=database,
            deployment_id=deployment.id,
            step_name=current_step,
            error_message=str(error),
        )

        deployment.status = "failed"
        deployment.error_message = str(error)[:5000]

        database.commit()

        raise DeploymentPrepareError(
            str(error)
        ) from error

    except Exception as error:
        deployment.status = "failed"
        deployment.error_message = (
            "Deployment hazırlığı sırasında beklenmeyen hata oluştu."
        )

        database.commit()

        raise DeploymentPrepareError(
            "Deployment hazırlığı sırasında beklenmeyen hata oluştu."
        ) from error