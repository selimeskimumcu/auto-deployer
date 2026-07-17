from pydantic import BaseModel,Field

class SSHConnectionTestRequest(BaseModel):
    password: str = Field(
        min_length=1,
        max_length=256,
    )


class SHHConnectionTestResponse(BaseModel):
    connected: bool
    hostname: str | None = None
    remote_username: str | None = None
    operating_system: str | None = None
    docker_installed: bool = False
    docker_version: str | None = None
    docker_accessible: bool = False
    message: str
    