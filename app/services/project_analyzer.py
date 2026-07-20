from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ProjectAnalysis:
    project_type: str
    framework: str | None
    dockerfile_exists: bool
    dockerfile_path: str | None
    compose_file_exists: bool
    compose_file_path: str | None
    dependency_file: str | None
    suggested_build_command: str | None
    suggested_start_command: str | None
    suggested_port: int | None
    health_endpoint: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def find_first_file(
    workspace: Path,
    filenames: list[str],
) -> Path | None:
    for filename in filenames:
        candidate = workspace / filename

        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def find_dotnet_project(
    workspace: Path,
) -> Path | None:
    project_files = list(workspace.glob("*.csproj"))

    if project_files:
        return project_files[0]

    nested_project_files = list(
        workspace.glob("*/*.csproj")
    )

    if nested_project_files:
        return nested_project_files[0]

    return None


def detect_python_framework(
    workspace: Path,
) -> str | None:
    searchable_files = [
        workspace / "requirements.txt",
        workspace / "pyproject.toml",
        workspace / "Pipfile",
    ]

    combined_content = ""

    for file_path in searchable_files:
        if not file_path.exists():
            continue

        try:
            combined_content += file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

        except OSError:
            continue

    if "fastapi" in combined_content:
        return "fastapi"

    if "django" in combined_content:
        return "django"

    if "flask" in combined_content:
        return "flask"

    return None


def detect_node_framework(
    workspace: Path,
) -> str | None:
    package_json = workspace / "package.json"

    if not package_json.exists():
        return None

    try:
        content = package_json.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

    except OSError:
        return None

    if '"next"' in content:
        return "nextjs"

    if '"nestjs' in content or '"@nestjs/' in content:
        return "nestjs"

    if '"express"' in content:
        return "express"

    if '"vite"' in content:
        return "vite"

    if '"react"' in content:
        return "react"

    return "node"


def analyze_python_project(
    workspace: Path,
    dockerfile: Path | None,
    compose_file: Path | None,
) -> ProjectAnalysis:
    dependency_file = find_first_file(
        workspace,
        [
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
        ],
    )

    framework = detect_python_framework(workspace)

    suggested_start_command: str | None = None
    suggested_port: int | None = None
    health_endpoint: str | None = None

    if framework == "fastapi":
        suggested_start_command = (
            "uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )
        suggested_port = 8000
        health_endpoint = "/health"

    elif framework == "django":
        suggested_start_command = (
            "python manage.py runserver 0.0.0.0:8000"
        )
        suggested_port = 8000
        health_endpoint = "/"

    elif framework == "flask":
        suggested_start_command = (
            "flask run --host=0.0.0.0 --port=5000"
        )
        suggested_port = 5000
        health_endpoint = "/"

    return ProjectAnalysis(
        project_type="python",
        framework=framework,
        dockerfile_exists=dockerfile is not None,
        dockerfile_path=(
            str(dockerfile.relative_to(workspace))
            if dockerfile
            else None
        ),
        compose_file_exists=compose_file is not None,
        compose_file_path=(
            str(compose_file.relative_to(workspace))
            if compose_file
            else None
        ),
        dependency_file=(
            str(dependency_file.relative_to(workspace))
            if dependency_file
            else None
        ),
        suggested_build_command=(
            "pip install -r requirements.txt"
            if dependency_file
            and dependency_file.name == "requirements.txt"
            else None
        ),
        suggested_start_command=suggested_start_command,
        suggested_port=suggested_port,
        health_endpoint=health_endpoint,
    )


def analyze_node_project(
    workspace: Path,
    dockerfile: Path | None,
    compose_file: Path | None,
) -> ProjectAnalysis:
    framework = detect_node_framework(workspace)

    lock_file = find_first_file(
        workspace,
        [
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        ],
    )

    build_command = "npm run build"
    start_command = "npm start"
    port = 3000

    if framework == "vite":
        start_command = "npm run preview -- --host 0.0.0.0"
        port = 4173

    elif framework == "express":
        start_command = "npm start"
        port = 3000

    elif framework == "nestjs":
        start_command = "npm run start:prod"
        port = 3000

    return ProjectAnalysis(
        project_type="node",
        framework=framework,
        dockerfile_exists=dockerfile is not None,
        dockerfile_path=(
            str(dockerfile.relative_to(workspace))
            if dockerfile
            else None
        ),
        compose_file_exists=compose_file is not None,
        compose_file_path=(
            str(compose_file.relative_to(workspace))
            if compose_file
            else None
        ),
        dependency_file=(
            str(lock_file.relative_to(workspace))
            if lock_file
            else "package.json"
        ),
        suggested_build_command=build_command,
        suggested_start_command=start_command,
        suggested_port=port,
        health_endpoint="/",
    )


def analyze_dotnet_project(
    workspace: Path,
    dotnet_project: Path,
    dockerfile: Path | None,
    compose_file: Path | None,
) -> ProjectAnalysis:
    project_name = dotnet_project.stem

    return ProjectAnalysis(
        project_type="dotnet",
        framework="aspnet-core",
        dockerfile_exists=dockerfile is not None,
        dockerfile_path=(
            str(dockerfile.relative_to(workspace))
            if dockerfile
            else None
        ),
        compose_file_exists=compose_file is not None,
        compose_file_path=(
            str(compose_file.relative_to(workspace))
            if compose_file
            else None
        ),
        dependency_file=str(
            dotnet_project.relative_to(workspace)
        ),
        suggested_build_command="dotnet publish -c Release",
        suggested_start_command=f"dotnet {project_name}.dll",
        suggested_port=8080,
        health_endpoint="/health",
    )


def analyze_project(
    workspace: Path,
) -> ProjectAnalysis:
    dockerfile = find_first_file(
        workspace,
        [
            "Dockerfile",
            "dockerfile",
        ],
    )

    compose_file = find_first_file(
        workspace,
        [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ],
    )

    dotnet_project = find_dotnet_project(workspace)

    if (
        (workspace / "requirements.txt").exists()
        or (workspace / "pyproject.toml").exists()
        or (workspace / "Pipfile").exists()
    ):
        return analyze_python_project(
            workspace=workspace,
            dockerfile=dockerfile,
            compose_file=compose_file,
        )
    
    if dotnet_project is not None:
        return analyze_dotnet_project(
            workspace=workspace,
            dotnet_project=dotnet_project,
            dockerfile=dockerfile,
            compose_file=compose_file,
        )
    
    return ProjectAnalysis(
        project_type ="unknown",
        framework=None,
        dockerfile_exists=dockerfile is not None,
        dockerfile_path=(
            str(compose_file.relative_to(workspace))
            if compose_file
            else None
        ),
        dependency_file= None,
        suggested_build_command=None,
        suggested_start_command=None,
        suggested_port=None,
        health_endpoint=None,
    )