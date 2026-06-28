from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    industry: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
    recruiters: Mapped[list[Recruiter]] = relationship(back_populates="company")


class Recruiter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recruiters"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL")
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company | None] = relationship(back_populates="recruiters")
    contacts: Mapped[list[Contact]] = relationship(back_populates="recruiter")
    messages: Mapped[list["Message"]] = relationship(back_populates="recruiter")


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruiters.id", ondelete="CASCADE")
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    recruiter: Mapped[Recruiter | None] = relationship(back_populates="contacts")
