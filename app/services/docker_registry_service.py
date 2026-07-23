import re
import subprocess
from dataclasses import dataclass


@dataclass
class DockerPushResult:
    local_image_tag: str
    registry_image_tag: str
    digest: str | None
    push_logs: str


def normalize_registry_component(value: str) -> str:
    normalized_value = value.strip().lower()

    normalized_value = re.sub(
        pattern=r"[^a-z0-9._-]+",
        repl="-",
        string=normalized_value,
    )

    normalized_value = normalized_value.strip(".-_")

    if not normalized_value:
        raise ValueError(
            "Registry image adı oluşturulamadı."
        )

    return normalized_value


def create_registry_image_tag(
    registry: str,
    namespace: str,
    deployment_id,
    tag: str = "latest",
) -> str:
    clean_registry = registry.strip().rstrip("/")
    clean_namespace = normalize_registry_component(namespace)

    short_deployment_id = str(deployment_id).split("-")[0]

    image_name = normalize_registry_component(
        f"auto-deployer-{short_deployment_id}"
    )

    clean_tag = normalize_registry_component(tag)

    return (
        f"{clean_registry}/"
        f"{clean_namespace}/"
        f"{image_name}:"
        f"{clean_tag}"
    )


def login_to_registry(
    registry: str,
    username: str,
    token: str,
) -> None:
    if not username.strip():
        raise ValueError(
            "Registry kullanıcı adı boş olamaz."
        )

    if not token.strip():
        raise ValueError(
            "Registry token değeri boş olamaz."
        )

    command = [
        "docker",
        "login",
        registry,
        "--username",
        username,
        "--password-stdin",
    ]

    try:
        result = subprocess.run(
            command,
            input=token,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    except FileNotFoundError as exception:
        raise RuntimeError(
            "Docker komutu bulunamadı."
        ) from exception

    except subprocess.TimeoutExpired as exception:
        raise RuntimeError(
            "Docker registry giriş işlemi zaman aşımına uğradı."
        ) from exception

    if result.returncode != 0:
        login_error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Bilinmeyen registry giriş hatası."
        )

        raise RuntimeError(
            f"Docker registry girişi başarısız: {login_error}"
        )


def tag_docker_image(
    local_image_tag: str,
    registry_image_tag: str,
) -> None:
    command = [
        "docker",
        "image",
        "tag",
        local_image_tag,
        registry_image_tag,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    if result.returncode != 0:
        tag_error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Bilinmeyen Docker tag hatası."
        )

        raise RuntimeError(
            f"Docker image tag işlemi başarısız: {tag_error}"
        )


def push_docker_image(
    registry_image_tag: str,
) -> tuple[str, str | None]:
    command = [
        "docker",
        "image",
        "push",
        registry_image_tag,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )

    except subprocess.TimeoutExpired as exception:
        raise RuntimeError(
            "Docker image push işlemi 30 dakikalık "
            "zaman aşımına uğradı."
        ) from exception

    push_logs = "\n".join(
        log_part
        for log_part in [
            result.stdout.strip(),
            result.stderr.strip(),
        ]
        if log_part
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker image push başarısız oldu.\n{push_logs}"
        )

    digest = extract_digest(push_logs)

    return push_logs, digest


def extract_digest(push_logs: str) -> str | None:
    digest_match = re.search(
        pattern=r"digest:\s*(sha256:[a-fA-F0-9]{64})",
        string=push_logs,
        flags=re.IGNORECASE,
    )

    if digest_match is None:
        return None

    return digest_match.group(1).lower()


def publish_docker_image(
    local_image_tag: str,
    registry: str,
    namespace: str,
    username: str,
    token: str,
    deployment_id,
) -> DockerPushResult:
    registry_image_tag = create_registry_image_tag(
        registry=registry,
        namespace=namespace,
        deployment_id=deployment_id,
    )

    login_to_registry(
        registry=registry,
        username=username,
        token=token,
    )

    tag_docker_image(
        local_image_tag=local_image_tag,
        registry_image_tag=registry_image_tag,
    )

    push_logs, digest = push_docker_image(
        registry_image_tag=registry_image_tag,
    )

    return DockerPushResult(
        local_image_tag=local_image_tag,
        registry_image_tag=registry_image_tag,
        digest=digest,
        push_logs=push_logs,
    )