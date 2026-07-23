from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

WORKSPACE_ROOT = BASE_DIR / "workspace"

class Settings(BaseSettings):
    app_name: str = "Auto Deployer API"
    app_version: str = "0.1.0"
    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    ghcr_registry: str = "ghcr.io"
    ghcr_username: str
    ghcr_token: str
    ghcr_namespace: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()