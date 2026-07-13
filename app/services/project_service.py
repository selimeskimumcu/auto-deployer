import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

def create_project(
        database: Session,
        owner_id: uuid.UUID,
        project_data: ProjectCreate,
) -> Project:
    project = Project(
        owner_id=owner_id,
        name=project_data.name.strip(),
        description = project_data.description,
        repository_provider=project_data.repository_provider,
        repository_url=str(project_data.repository_url),
        branch=project_data.branch.strip(),
    )

    database.add(project)
    database.commit()
    database.refresh(project)

    return project


def get_projects_by_owner(
        database: Session,
        owner_id: uuid.UUID,
) -> list[Project]:
    statement = (
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc())
    )

    return list(database.scalars(statement).all())

def get_project_by_id_and_owner(
        databese: Session,
        project_id: uuid.UUID,
        owner_id: uuid.UUID,
) -> Project | None:
    statement = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )

    return databese.scalar(statement)



def update_project(
        database: Session,
        project: Project,
        project_data:ProjectUpdate,
) -> Project:
    update_data = project_data.model_dump(
        exclude_unset=True,
    )
    
    if "repository_url" in update_data:
        update_data["repository_url"] = str(
            update_data["repository_url"]
        )

    for field_name, field_value in update_data.items():
        if isinstance(field_value, str):
            field_value = field_value.strip()

        setattr(project, field_name,field_value)

    database.commit()
    database.refresh(project)

    return project


def delete_project(
        database: Session,
        project: Project,
) -> None:
    database.delete(project)
    database.commit()