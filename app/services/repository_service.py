import shutil
import subprocess
import uuid
from pathlib import Path

from app.config import WORKSPACE_ROOT


class RepositoryError(Exception):
    pass


def get_workspace_path(
    deployment_id: uuid.UUID,
) -> Path:
    return WORKSPACE_ROOT / str(deployment_id)


def run_git_command(
    arguments: list[str],
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except FileNotFoundError as error:
        raise RepositoryError(
            "Git sistemde kurulu değil veya PATH içinde bulunamadı."
        ) from error

    except subprocess.TimeoutExpired as error:
        raise RepositoryError(
            "Git işlemi zaman aşımına uğradı."
        ) from error


def clone_repository(
    repository_url: str,
    branch: str,
    deployment_id: uuid.UUID,
) -> Path:
    workspace = get_workspace_path(deployment_id)

    if workspace.exists():
        shutil.rmtree(workspace)

    workspace.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result = run_git_command(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
            "--branch",
            branch,
            repository_url,
            str(workspace),
        ]
    )

    if result.returncode != 0:
        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Repository clone işlemi başarısız oldu."
        )

        raise RepositoryError(error_message)

    return workspace


def get_commit_sha(
    workspace: Path,
) -> str:
    result = run_git_command(
        [
            "git",
            "-C",
            str(workspace),
            "rev-parse",
            "HEAD",
        ],
        timeout=30,
    )

    if result.returncode != 0:
        raise RepositoryError(
            result.stderr.strip()
            or "Commit SHA alınamadı."
        )

    commit_sha = result.stdout.strip()

    if len(commit_sha) != 40:
        raise RepositoryError(
            "Geçerli bir Git commit SHA değeri alınamadı."
        )

    return commit_sha


def remove_workspace(
    deployment_id: uuid.UUID,
) -> None:
    workspace = get_workspace_path(deployment_id)

    if workspace.exists():
        shutil.rmtree(workspace)