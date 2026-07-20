from dataclasses import dataclass
from pathlib import Path


@dataclass
class DockerfileResult:
    dockerfile_path: str
    generated: bool
    content: str


FASTAPI_DOCKERFILE = """FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


FLASK_DOCKERFILE = """FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
"""


DJANGO_DOCKERFILE = """FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"""


NODE_DOCKERFILE = """FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
"""


DOTNET_DOCKERFILE = """FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

COPY . .

RUN dotnet restore
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0

WORKDIR /app

COPY --from=build /app/publish .

EXPOSE 8080

ENTRYPOINT ["dotnet", "Application.dll"]
"""

def generate_dockerfile(
        workspace_path: str,
        framework: str | None,
        project_type: str | None = None,
) -> DockerfileResult:
    """
    Workspace içinde Dockerfile varsa onu kullanır.
    Yoksa framework veya proje tipine göre yeni Dockerfile üretir.
    """
    workspace = Path(workspace_path)

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace bulunamadı: {workspace_path}"
        )
    
    if not workspace.is_dir():
        raise NotADirectoryError(
            f"Workspace yolu klasör değil: {workspace_path}"
        )
    
    dockerfile_path = workspace / "Dockerfile"

    if dockerfile_path.exists():
        existing_content = dockerfile_path.read_text(
            encoding="utf-8"
        )

        return DockerfileResult(
            dockerfile_path=str(dockerfile_path),
            generated=False,
            content=existing_content,
        )
    
    normalized_framework = (framework or "").strip().lower()
    normalized_project_type = (project_type or "").strip().lower()

    if normalized_framework =="fastapi":
        content = FASTAPI_DOCKERFILE

    elif normalized_framework == "flask":
        content = FLASK_DOCKERFILE

    elif normalized_framework == "django":
        content = DJANGO_DOCKERFILE

    elif normalized_framework in {
        "dotnet",
        ".net",
        "nextjs",
        "react",
        "vite",
    }:
        content = NODE_DOCKERFILE

    elif normalized_framework in {
        "dotnet",
        ".net",
        "asp.net",
        "asp.net core",
    }:
        content = DOTNET_DOCKERFILE

    elif normalized_framework in {
        "node",
        "nodejs",
        "javascript",
        "typescript",
    }:
        content = NODE_DOCKERFILE

    elif normalized_framework in {
        "dotnet",
        ".net",
        "csharp",
        "c#",
    }:
        content = DOTNET_DOCKERFILE

    else:
        raise ValueError(
            "Bu proje için otomatik Dockerfile şablonu bulunamadı. "
            f"project_tpye={project_type}, frameworkk={framework}"
        )
    
    dockerfile_path.write_text(
        content,
        encoding="utf-8",
    )

    return DockerfileResult(
        dockerfile_path=str(dockerfile_path),
        generated=True,
        content=content,
    )