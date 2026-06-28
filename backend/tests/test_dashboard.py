from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.api.routes.dashboard import application_count, infer_company_type, scalar_count
from backend.app.services.job_search import canonicalize_source_url, extract_applicant_count, extract_contacts_from_text
from shared.constants import ApplicationStatus


@pytest.mark.asyncio
async def test_scalar_count_returns_database_count() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 7
    session.execute.return_value = result

    count = await scalar_count(session, object())  # type: ignore[arg-type]

    assert count == 7


@pytest.mark.asyncio
async def test_application_count_filters_by_status() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 3
    session.execute.return_value = result

    count = await application_count(session, ApplicationStatus.APPLIED)

    assert count == 3
    statement = session.execute.call_args.args[0]
    assert "applications.status" in str(statement)


def test_extract_contacts_from_text_picks_up_emails_and_recruiter_lines() -> None:
    text = """
    Jane Doe - Technical Recruiter
    jane.doe@example.com
    https://www.linkedin.com/in/jane-doe-hr/
    """

    contacts = extract_contacts_from_text(text, source_url="https://example.com/job", source_name="linkedin")

    assert any(contact.email == "jane.doe@example.com" for contact in contacts)
    assert any(contact.full_name == "Jane Doe" for contact in contacts)


def test_canonicalize_source_url_removes_tracking_query_params() -> None:
    url = "https://www.linkedin.com/jobs/view/test-role-at-acme-12345/?position=12&pageNum=0&trackingId=abc"

    assert canonicalize_source_url(url) == "https://www.linkedin.com/jobs/view/test-role-at-acme-12345"


def test_extract_applicant_count_reads_job_text() -> None:
    text = "12 applicants • Actively recruiting"

    assert extract_applicant_count(text) == 12


def test_infer_company_type_handles_obvious_mnc_names() -> None:
    assert infer_company_type("Microsoft") == "mnc"
