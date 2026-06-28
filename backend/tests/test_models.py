from backend.app.db.base import Base
from backend.app.models import Application, Company, Job, Skill, User
from shared.constants import JobSource


def test_core_tables_are_registered() -> None:
    expected_tables = {
        "api_keys",
        "application_answers",
        "application_events",
        "applications",
        "automation_logs",
        "companies",
        "contacts",
        "cover_letters",
        "follow_ups",
        "job_matches",
        "job_skills",
        "jobs",
        "messages",
        "recruiters",
        "resume_versions",
        "skills",
        "user_settings",
        "users",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_model_defaults_match_product_states() -> None:
    user = User(email="test@example.com", hashed_password="hash", full_name="Test User")
    company = Company(name="Acme")
    job = Job(title="AI Engineer", source=JobSource.LINKEDIN, source_url="https://example.com/job")
    skill = Skill(name="Python")
    application = Application(user=user, job=job)

    assert company.name == "Acme"
    assert skill.name == "Python"
    assert job.source == JobSource.LINKEDIN
    assert application.__table__.columns["status"].default is not None
