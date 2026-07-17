import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict



DeploymentStatus = Literal[
    "queued",
    "cloning",
    "analyzing",
    "building",
    "connecting"
    "provisioning"
    "deploying",
    "verifying",
    "succeeded",
    "failed",
    "cancelled",
    "rolling_back",
]

DeploymentStatus = Literal[
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
]

class DeploymentCreate(BaseModel):
    environment_id: uuid.UUID


class DeploymentStepResponse(BaseModel):
    id: uuid.UUID
    deployment_id: uuid.UUID
    step_order: int
    name: str
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)



class DeploymentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    environment_id: uuid.UUID
    started_by_user_id: uuid.UUID
    version_number: int
    branch: str
    commit_sha: str | None
    status: str
    image_tag: str | None
    container_name: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeploymentDetailResponse(DeploymentResponse):
    steps: list[DeploymentResponse]