import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


RepositoryProvider = Literal["github", "azure_devops"]


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    repository_provider: RepositoryProvider

    repository_url: HttpUrl

    branch: str = Field(
        default="main",
        min_length=1,
        max_length=150,
    )


class ProjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    repository_provider: RepositoryProvider | None = None

    repository_url: HttpUrl | None = None

    branch: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )


class ProjectResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    repository_provider: str
    repository_url: str
    branch: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)