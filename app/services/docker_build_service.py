import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DockerBuildResult:
    image_tag: str
    image_id: str | None
    build_logs: str


def create_image_tag(deployment_id: uuid.UUID) -> str:
    short_deployment_id = str(deployment_id).split("-")[0]

    return f"autodeployer-{short_deployment_id}:latest"


def validate_image_tag(image_tag: str) -> None:
    pattern = r"^[a-z0-9][a-z0-9._/-]*:[a-zA-Z0-9._-]+$"

    if re.fullmatch(pattern, image_tag) is None:
        raise ValueError("Geçersiz Docker image tag değeri.")


def build_docker_image(
    workspace_path: Path,
    deployment_id: uuid.UUID,
) -> DockerBuildResult:
    workspace_path = workspace_path.resolve()

    if not workspace_path.exists():
        raise FileNotFoundError(
            f"Workspace klasörü bulunamadı: {workspace_path}"
        )

    if not workspace_path.is_dir():
        raise ValueError(
            f"Workspace yolu bir klasör değil: {workspace_path}"
        )

    dockerfile_path = workspace_path / "Dockerfile"

    if not dockerfile_path.exists():
        raise FileNotFoundError(
            f"Dockerfile bulunamadı: {dockerfile_path}"
        )

    image_tag = create_image_tag(deployment_id)

    validate_image_tag(image_tag)

    command = [
        "docker",
        "build",
        "--tag",
        image_tag,
        "--file",
        str(dockerfile_path),
        str(workspace_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )

    except FileNotFoundError as exception:
        raise RuntimeError(
            "Docker komutu bulunamadı. Docker'ın kurulu ve çalışır "
            "durumda olduğunu kontrol edin."
        ) from exception

    except subprocess.TimeoutExpired as exception:
        raise RuntimeError(
            "Docker image build işlemi 15 dakikalık zaman aşımına uğradı."
        ) from exception

    build_logs = "\n".join(
        part
        for part in [
            result.stdout.strip(),
            result.stderr.strip(),
        ]
        if part
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker image build başarısız oldu.\n{build_logs}"
        )

    image_id = get_docker_image_id(image_tag)

    return DockerBuildResult(
        image_tag=image_tag,
        image_id=image_id,
        build_logs=build_logs,
    )


def get_docker_image_id(image_tag: str) -> str | None:
    result = subprocess.run(
        [
            "docker",
            "image",
            "inspect",
            image_tag,
            "--format",
            "{{.Id}}",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    if result.returncode != 0:
        return None

    image_id = result.stdout.strip()

    return image_id or None