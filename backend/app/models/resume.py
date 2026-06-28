from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResumeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    user: Mapped["User"] = relationship(back_populates="resume_versions")
    applications: Mapped[list["Application"]] = relationship(back_populates="resume_version")
