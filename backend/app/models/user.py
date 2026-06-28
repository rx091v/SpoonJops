from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    settings: Mapped[UserSettings | None] = relationship(back_populates="user")
    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="user")
    resume_versions: Mapped[list["ResumeVersion"]] = relationship(back_populates="user")
    applications: Mapped[list["Application"]] = relationship(back_populates="user")


class UserSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    target_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    minimum_salary: Mapped[int | None] = mapped_column(Integer)
    excluded_companies: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="settings")


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (UniqueConstraint("user_id", "provider"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="api_keys")
