from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from shared.constants import JobSource


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_url"),
        Index("ix_jobs_company_id", "company_id"),
        Index("ix_jobs_source_external_id", "source", "external_id"),
    )

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[JobSource] = mapped_column(
        Enum(JobSource, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    remote_type: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    company: Mapped["Company | None"] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")
    skills: Mapped[list[JobSkill]] = relationship(back_populates="job")


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(120))

    jobs: Mapped[list[JobSkill]] = relationship(back_populates="skill")


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    required: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    job: Mapped[Job] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="jobs")
