import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.deployment import Deployment, DeploymentStep
from app.models.environment import Environment
from app.models.project import Project


DEPLOYMENT_STEP_NAMES = [
    "ValidateRequest",
    "CreateWorkspace",
    "CloneRepository",
    "ResolveCommit",
    "AnalyzeProject",
    "PrepareDockerfile",
    "BuildImage",
    "ConnectServer",
    "InspectServer",
    "EnsureDocker",
    "TransferImage",
    "StartCandidate",
    "VerifyHealth",
    "PromoteVersion",
    "PersistVersion",
    "Cleanup",
]


class EnvironmentNotFoundError(Exception):
    pass

def get_owned_environment(
        database: Session,
        environment_id: uuid.UUID,
        owner_id: uuid.UUID,
) -> Environment | None:
    statement = (
        select(Environment)
        .join(Project, Environment.project_id == Project.id)
        .where(
            Environment.id == environment_id,
            Project.owner_id == owner_id,
        )
    )

    return database.scalar(statement)

def get_next_version_number(
        database: Session,
        environment_id: uuid.UUID,
) -> int:
    current_maximum = database.scalar(
        select(func.max(Deployment.version_number)).where(
            Deployment.environment_id == environment_id,
        )
    )

    return (current_maximum or 0) + 1


def create_deployment(
        database: Session,
        environment_id: uuid.UUID,
        owner_id: uuid.UUID,
        started_by_user_id: uuid.UUID,
) -> Deployment:
    environment = get_owned_environment(
        database=database,
        environment_id=environment_id,
        owner_id=owner_id,
    )

    if environment is None:
        raise EnvironmentNotFoundError(
            "Environment bulunamadı."
        )
    
    project = database.get(
        Project,
        environment.project_id,
    )

    if project is None:
        raise EnvironmentNotFoundError(
            "Environment projesi bulunamadı."
        )
    
    version_number = get_next_version_number(
        database=database,
        environment_id= environment.id,
    )

    deployment = Deployment(
        project_id = project.id,
        environment_id = environment.id,
        started_by_user_id= started_by_user_id,
        version_number=version_number,
        branch = project.branch,
        status = "queued",
    )

    database.add(deployment)
    database.flush()


    steps = [
        DeploymentStep(
            deployment_id= deployment.id,
            step_order = index,
            name = step_name,
            status = "pending",
        )
        for index, step_name in enumerate(
            DEPLOYMENT_STEP_NAMES,
            start=1,
        )
    ]

    database.add_all(steps)
    database.commit()
    database.refresh(deployment)

    return deployment


def list_deployments_by_owner(
        database: Session,
        owner_id:uuid.UUID,
) -> list[Deployment]:
    statement = (
        select(Deployment)
        .join(Project,Deployment.project_id == Project.id)
        .where(Project.owner_id == owner_id)
        .order_by(Deployment.created_at.desc())
    )

    return list(
        database.scalars(statement).all()
    )

def get_deployment_by_id_and_owner(
        database: Session,
        deployment_id: uuid.UUID,
        owner_id: uuid.UUID,
) -> Deployment | None:
    statement = (
        select(Deployment)
        .join(Project, Deployment.project_id == Project.id)
        .where(
            Deployment.id == deployment_id,
            Project.owner_id == owner_id,
        )
    )

    return database.scalar(statement)


def get_deployment_steps(
        database: Session,
        deployment_id: uuid.UUID,
) -> list[DeploymentStep]:
    statement = (
        select(DeploymentStep)
        .where(
            DeploymentStep.deployment_id == deployment_id,
        )
        .order_by(DeploymentStep.step_order.asc())
    )

    return list(
        database.scalars(statement).all()
    )