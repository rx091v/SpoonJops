"""initial schema

Revision ID: 20260628_0001
Revises:
Create Date: 2026-06-28 20:45:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260628_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


application_status = postgresql.ENUM(
    "saved",
    "applied",
    "rejected",
    "interview",
    "offer",
    name="applicationstatus",
    create_type=False,
)
job_source = postgresql.ENUM(
    "linkedin",
    "instahyre",
    "naukri",
    "indeed",
    "wellfound",
    "greenhouse",
    "lever",
    "ashby",
    "company",
    name="jobsource",
    create_type=False,
)


def upgrade() -> None:
    application_status.create(op.get_bind(), checkfirst=True)
    job_source.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("target_titles", sa.JSON(), nullable=False),
        sa.Column("target_locations", sa.JSON(), nullable=False),
        sa.Column("remote_only", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("minimum_salary", sa.Integer(), nullable=True),
        sa.Column("excluded_companies", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider"),
    )
    op.create_table(
        "recruiters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source", job_source, nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("remote_type", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_url"),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_source_external_id", "jobs", ["source", "external_id"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("recruiter_id", sa.UUID(), nullable=True),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "resume_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("resume_version_id", sa.UUID(), nullable=True),
        sa.Column("status", application_status, server_default="saved", nullable=False),
        sa.Column("match_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_version_id"], ["resume_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id"),
    )
    op.create_table(
        "job_skills",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id", "skill_id"),
    )
    op.create_table(
        "application_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "application_answers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cover_letters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("recruiter_id", sa.UUID(), nullable=True),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "job_matches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "automation_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("task_name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table_name in (
        "automation_logs",
        "job_matches",
        "follow_ups",
        "messages",
        "cover_letters",
        "application_answers",
        "application_events",
        "job_skills",
        "applications",
        "resume_versions",
        "contacts",
        "jobs",
        "recruiters",
        "api_keys",
        "user_settings",
        "skills",
        "companies",
        "users",
    ):
        op.drop_table(table_name)

    job_source.drop(op.get_bind(), checkfirst=True)
    application_status.drop(op.get_bind(), checkfirst=True)
