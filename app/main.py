from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.environments import router as environments_router

from app.config import settings
from app.database import get_database_session


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automatic deployment management platform API",
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(environments_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Auto Deployer API çalışıyor",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": settings.app_name,
    }


@app.get("/health/database")
def database_health_check(
    database: Session = Depends(get_database_session),
) -> dict[str, str]:
    try:
        database.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "PostgreSQL",
            "connection": "successful",
        }

    except SQLAlchemyError as error:
        print(f"Database error: {error}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL bağlantısı kurulamadı.",
        ) from error