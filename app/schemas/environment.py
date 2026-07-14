import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


EnvironmentType = Literal[
    "linux_docker",
    "windows_iis",
    "aws_eks",
]


class EnvironmentCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    environment_type: EnvironmentType = "linux_docker"

    host: str = Field(
        min_length=1,
        max_length=255,
    )

    ssh_port: int = Field(
        default=22,
        ge=1,
        le=65535,
    )

    username: str = Field(
        min_length=1,
        max_length=100,
    )

    application_port: int = Field(
        ge=1,
        le=65535,
    )

    container_port: int = Field(
        ge=1,
        le=65535,
    )

    domain: str | None = Field(
        default=None,
        max_length=255,
    )

    is_production: bool = False

    @field_validator(
        "name",
        "host",
        "username",
        "domain",
        mode="before",
    )
    @classmethod
    def strip_string_values(
        cls,
        value: str | None,
    ) -> str | None:
        if isinstance(value, str):
            value = value.strip()

        return value


class EnvironmentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    environment_type: EnvironmentType | None = None

    host: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    ssh_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )

    username: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    application_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )

    container_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )

    domain: str | None = Field(
        default=None,
        max_length=255,
    )

    is_production: bool | None = None
    is_active: bool | None = None

    @field_validator(
        "name",
        "host",
        "username",
        "domain",
        mode="before",
    )
    @classmethod
    def strip_string_values(
        cls,
        value: str | None,
    ) -> str | None:
        if isinstance(value, str):
            value = value.strip()

        return value


class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    environment_type: str
    host: str
    ssh_port: int
    username: str
    application_port: int
    container_port: int
    domain: str | None
    is_production: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )