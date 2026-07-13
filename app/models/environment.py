import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Environment(Base):
    __tablename__ = "environments"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_environments_project_name",
        ),
        CheckConstraint(
            "ssh_port BETWEEN 1 AND 65535",
            name="ck_environments_ssh_port",
        ),
        CheckConstraint(
            "application_port BETWEEN 1 AND 65535",
            name="ck_environments_application_port",
        ),
        CheckConstraint(
            "container_port BETWEEN 1 AND 65535",
            name="ck_environments_container_port",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    environment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="linux_docker",
    )

    host: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ssh_port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=22,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    application_port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    container_port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_production: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )