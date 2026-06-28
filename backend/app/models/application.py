from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from shared.constants import ApplicationStatus


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL")
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=ApplicationStatus.SAVED,
        server_default=ApplicationStatus.SAVED.value,
    )
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship(back_populates="applications")
    resume_version: Mapped["ResumeVersion | None"] = relationship(back_populates="applications")
    events: Mapped[list[ApplicationEvent]] = relationship(back_populates="application")
    answers: Mapped[list[ApplicationAnswer]] = relationship(back_populates="application")
    cover_letters: Mapped[list[CoverLetter]] = relationship(back_populates="application")
    messages: Mapped[list[Message]] = relationship(back_populates="application")
    follow_ups: Mapped[list[FollowUp]] = relationship(back_populates="application")
    matches: Mapped[list[JobMatch]] = relationship(back_populates="application")


class ApplicationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    application: Mapped[Application] = relationship(back_populates="events")


class ApplicationAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_answers"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    application: Mapped[Application] = relationship(back_populates="answers")


class CoverLetter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cover_letters"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))

    application: Mapped[Application] = relationship(back_populates="cover_letters")


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruiters.id", ondelete="SET NULL")
    )
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped[Application | None] = relationship(back_populates="messages")
    recruiter: Mapped["Recruiter | None"] = relationship(back_populates="messages")
    follow_ups: Mapped[list[FollowUp]] = relationship(back_populates="message")


class FollowUp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "follow_ups"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped[Application] = relationship(back_populates="follow_ups")
    message: Mapped[Message | None] = relationship(back_populates="follow_ups")


class JobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_matches"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)

    application: Mapped[Application] = relationship(back_populates="matches")


class AutomationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automation_logs"

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL")
    )
    task_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
