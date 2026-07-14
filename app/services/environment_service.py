from uuid import UUID

from sqlalchemy.orm import Session

from app.models.environment import Environment
from app.models.project import Project
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentUpdate,
)

def create_environment(
        database: Session,
        project_id: UUID,
        owner_id: UUID,
        environment_data: EnvironmentCreate,
) -> Environment:
    project = (
        database.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )
        .first()
    )

    if project is None:
        raise ValueError(
            "Project not found."
        )
    
    environment = Environment(
        project_id=project_id,
        name=environment_data.name,
        environment_type=environment_data.environment_type,
        host=environment_data.host,
        ssh_port=environment_data.ssh_port,
        username=environment_data.username,
        application_port=environment_data.application_port,
        container_port=environment_data.container_port,
        domain=environment_data.domain,
        is_production=environment_data.is_production,
    )

    database.add(environment)
    
    database.commit()

    database.refresh(environment)

    return environment

def list_project_environments(
        database: Session,
        project_id: UUID,
        owner_id: UUID,
):
    
    return(
        database.query(Environment)
        .join(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )
        .all()
    )

def get_environment(
        database: Session,
        environment_id: UUID,
        owner_id: UUID,
):
    
    return (
        database.query(Environment)
        .join(Project)
        .filter(
            Environment.id == environment_id,
            Project.owner_id == owner_id,
        )
        .first()
    )

def delete_environment(
        database: Session,
        environment: Environment,
):
    database.delete(environment)

    database.commit()

def update_environment(
        database: Session,
        environment: Environment,
        update_data: EnvironmentUpdate,
):
    
    for field, value in (
        update_data.model_dump(
            exclude_unset=True
        ).items()
    ):
        setattr(
            environment,
            field,
            value,
        )

        database.commit()

        database.refresh(environment)

        return environment