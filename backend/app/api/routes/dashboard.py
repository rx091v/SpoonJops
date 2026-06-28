from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from math import ceil
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db_session
from backend.app.models import Application, Company, Job, JobSkill, Recruiter
from backend.app.schemas.dashboard import DashboardSummary, FunnelPoint
from backend.app.schemas.jobs import (
    CompanyPagination,
    CompanySummary,
    JobContact,
    JobDetail,
    JobPagination,
    JobLink,
    RecruiterDetail,
    RecruiterPagination,
)
from backend.app.services.job_search import SearchProfile, build_profile, normalize_text
from backend.app.services.search_index import search_job_ids
from shared.constants import ApplicationStatus, JobSource

router = APIRouter()
MAX_PAGE_SIZE = 100

MNC_HINTS = {
    "accenture",
    "adobe",
    "amazon",
    "apple",
    "bloomberg",
    "capgemini",
    "cognizant",
    "deloitte",
    "deutsche telekom",
    "facebook",
    "google",
    "hcl",
    "ibm",
    "infosys",
    "intel",
    "microsoft",
    "nvidia",
    "oracle",
    "roku",
    "salesforce",
    "sap",
    "servicenow",
    "tcs",
    "uber",
    "walmart",
    "wipro",
}

STARTUP_HINTS = {
    "foundry",
    "labs",
    "startup",
    "studio",
    "ventures",
}


@dataclass(slots=True)
class JobScores:
    skill_match_score: float
    recency_score: float
    applicant_score: float
    weighted_score: float


async def scalar_count(session: AsyncSession, statement: Select[tuple[int]]) -> int:
    result = await session.execute(statement)
    return result.scalar_one()


async def application_count(session: AsyncSession, status: ApplicationStatus) -> int:
    result = await session.execute(
        select(func.count()).select_from(Application).where(Application.status == status)
    )
    return result.scalar_one()


def recruiter_to_contact(recruiter: Recruiter) -> JobContact:
    return JobContact(
        full_name=recruiter.full_name,
        title=recruiter.title,
        email=recruiter.email,
        linkedin_url=recruiter.linkedin_url,
        notes=recruiter.notes,
    )


def parse_applicant_count(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(\d{1,4})\s+(?:applicants?|candidates?)\b", text, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def infer_company_type(company_name: str | None, description: str | None = None) -> str | None:
    haystack = normalize_text(" ".join(filter(None, [company_name, description])))
    if not haystack:
        return None
    if any(hint in haystack for hint in MNC_HINTS):
        return "mnc"
    if any(hint in haystack for hint in STARTUP_HINTS):
        return "startup"
    return None


def canonical_company_name(job: Job) -> str | None:
    if job.company and job.company.name:
        return job.company.name
    return guess_company_name(job.source.value, job.source_url)


def guess_company_name(source: str, source_url: str, fallback: str | None = None) -> str | None:
    if fallback:
        return fallback
    if source.lower() == "linkedin":
        match = re.search(r"-at-([a-z0-9-]+)-\d+", source_url)
        if match:
            return match.group(1).replace("-", " ").title()
    return None


def job_contacts(job: Job) -> list[JobContact]:
    if not job.company:
        return []
    return [recruiter_to_contact(recruiter) for recruiter in job.company.recruiters]


def score_job(job: Job, profile: SearchProfile, weights: dict[str, float]) -> JobScores:
    company_name = canonical_company_name(job)
    job_skill_terms = [
        normalize_text(job_skill.skill.name)
        for job_skill in job.skills
        if job_skill.skill and normalize_text(job_skill.skill.name)
    ]
    haystack = normalize_text(
        " ".join(
            filter(
                None,
                [
                    job.title,
                    company_name,
                    job.location,
                    job.remote_type,
                    job.description,
                    " ".join(job_skill_terms),
                ],
            )
        )
    )

    target_terms = [normalize_text(keyword) for keyword in profile.target_keywords if normalize_text(keyword)]
    matched_terms = [term for term in target_terms if term and term in haystack]
    skill_match_score = 0.0
    if target_terms:
        skill_match_score = round(min(100.0, (len(matched_terms) / len(target_terms)) * 100.0), 2)
    elif any(token in haystack for token in ("python", "java", "react", "backend", "frontend", "cloud")):
        skill_match_score = 25.0

    now = datetime.now(timezone.utc)
    if job.posted_at:
        age_days = max((now - job.posted_at).days, 0)
    elif job.discovered_at:
        age_days = max((now - job.discovered_at).days, 0)
    else:
        age_days = 30
    recency_score = round(max(0.0, 100.0 - min(age_days * 4.0, 100.0)), 2)

    applicant_count = parse_applicant_count(job.description)
    if applicant_count is None:
        applicant_score = 50.0
    else:
        applicant_score = round(max(0.0, 100.0 - min(float(applicant_count), 100.0)), 2)

    total_weight = sum(weights.values()) or 1.0
    weighted_score = round(
        (
            skill_match_score * weights["skill"]
            + recency_score * weights["recency"]
            + applicant_score * weights["applicants"]
        )
        / total_weight,
        2,
    )
    return JobScores(
        skill_match_score=skill_match_score,
        recency_score=recency_score,
        applicant_score=applicant_score,
        weighted_score=weighted_score,
    )


def job_matches_filters(
    job: Job,
    *,
    search: str | None,
    location: str | None,
    sources: list[JobSource],
    company_types: list[str],
    company_name_filter: str | None,
    remote_only: bool | None,
    min_applicants: int | None,
    max_applicants: int | None,
) -> bool:
    company_name = canonical_company_name(job)
    applicant_count = parse_applicant_count(job.description)
    company_type = infer_company_type(company_name, job.description)
    haystack = normalize_text(" ".join(filter(None, [job.title, company_name, job.location, job.description])))
    remote_haystack = normalize_text(" ".join(filter(None, [job.remote_type, job.location, job.description])))

    if search and normalize_text(search) not in haystack:
        return False
    if location and normalize_text(location) not in normalize_text(job.location):
        return False
    if sources and job.source not in sources:
        return False
    if company_types and (company_type or "unknown") not in company_types:
        return False
    if company_name_filter and company_name_filter.lower() not in normalize_text(company_name):
        return False
    if remote_only is True and "remote" not in remote_haystack:
        return False
    if remote_only is False and "remote" in remote_haystack:
        return False
    if min_applicants is not None and (applicant_count is None or applicant_count < min_applicants):
        return False
    if max_applicants is not None and (applicant_count is None or applicant_count > max_applicants):
        return False
    return True


def build_job_detail(job: Job, profile: SearchProfile, rank: int, weights: dict[str, float]) -> JobDetail:
    company_name = canonical_company_name(job)
    company_type = infer_company_type(company_name, job.description)
    scores = score_job(job, profile, weights)
    contacts = job_contacts(job)
    source_url = unescape(job.source_url)
    description = job.description
    skill_haystack = normalize_text(
        " ".join(
            filter(
                None,
                [
                    job.title,
                    job.description,
                    " ".join(
                        normalize_text(job_skill.skill.name)
                        for job_skill in job.skills
                        if job_skill.skill and normalize_text(job_skill.skill.name)
                    ),
                ],
            )
        )
    )
    if description and len(description) > 400:
        description = description[:400] + "..."

    return JobDetail(
        id=str(job.id),
        rank=rank,
        score=round(scores.weighted_score),
        skill_match_score=scores.skill_match_score,
        recency_score=scores.recency_score,
        applicant_count=parse_applicant_count(job.description),
        company_type=company_type,
        company_score=100.0 if company_type == "mnc" else 85.0 if company_type == "startup" else 50.0,
        applicant_score=scores.applicant_score,
        source=job.source.value,
        company=guess_company_name(job.source.value, source_url, company_name),
        title=job.title,
        location=job.location,
        remote=job.remote_type,
        source_url=source_url,
        matched_keywords=[
            keyword
            for keyword in profile.target_keywords
            if normalize_text(keyword) in skill_haystack
        ],
        reasons=[
            f"skill match {scores.skill_match_score:.0f}",
            f"recency {scores.recency_score:.0f}",
            f"applicant score {scores.applicant_score:.0f}",
        ],
        tailored_resume=None,
        description=description,
        discovered_at=job.discovered_at,
        contacts=contacts,
    )


def sort_jobs(items: list[tuple[Job, JobScores]], sort_by: str, sort_dir: str) -> list[tuple[Job, JobScores]]:
    reverse = sort_dir == "desc"

    def key(item: tuple[Job, JobScores]) -> object:
        job, scores = item
        company_name = canonical_company_name(job) or ""
        applicant_count = parse_applicant_count(job.description)
        if sort_by == "recency":
            return job.posted_at or job.discovered_at or datetime.min.replace(tzinfo=timezone.utc)
        if sort_by == "title":
            return job.title.lower()
        if sort_by == "company":
            return company_name.lower()
        if sort_by == "applicants":
            return applicant_count if applicant_count is not None else -1
        return scores.weighted_score

    return sorted(items, key=key, reverse=reverse)


def aggregate_companies(jobs: list[Job], profile: SearchProfile, weights: dict[str, float]) -> list[CompanySummary]:
    grouped: dict[str, list[tuple[Job, JobScores]]] = defaultdict(list)
    for job in jobs:
        company_name = canonical_company_name(job) or "Unknown"
        grouped[company_name].append((job, score_job(job, profile, weights)))

    summaries: list[CompanySummary] = []
    for company_name, items in grouped.items():
        scores = [item[1].weighted_score for item in items]
        applicant_counts = [
            applicant_count
            for applicant_count in (parse_applicant_count(item[0].description) for item in items)
            if applicant_count is not None
        ]
        latest_job_at = max(
            [job.posted_at or job.discovered_at for job, _ in items if job.posted_at or job.discovered_at],
            default=None,
        )
        source_count = len({job.source.value for job, _ in items})
        company_type = infer_company_type(company_name, items[0][0].description)
        summaries.append(
            CompanySummary(
                company=company_name,
                company_type=company_type,
                job_count=len(items),
                score=round(sum(scores) / len(scores), 2) if scores else None,
                latest_job_at=latest_job_at,
                avg_applicants=round(sum(applicant_counts) / len(applicant_counts), 2) if applicant_counts else None,
                source_count=source_count,
            )
        )
    return summaries


def build_job_link(job: Job) -> JobLink:
    return JobLink(
        id=str(job.id),
        title=job.title,
        source=job.source.value,
        source_url=job.source_url,
    )


def build_recruiter_detail(
    recruiter: Recruiter,
    *,
    location: str | None,
    search: str | None,
    sources: list[JobSource],
    company_types: list[str],
) -> RecruiterDetail:
    company = recruiter.company
    company_name = company.name if company else None
    jobs = list(company.jobs) if company else []
    filtered_jobs = [
        job
        for job in jobs
        if job_matches_filters(
            job,
            search=search,
            location=location,
            sources=sources,
            company_types=company_types,
            company_name_filter=company_name,
            remote_only=None,
            min_applicants=None,
            max_applicants=None,
        )
    ]
    filtered_jobs = sorted(
        filtered_jobs,
        key=lambda job: job.posted_at or job.discovered_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return RecruiterDetail(
        id=str(recruiter.id),
        full_name=recruiter.full_name,
        title=recruiter.title,
        email=recruiter.email,
        linkedin_url=recruiter.linkedin_url,
        notes=recruiter.notes,
        company=company_name,
        company_id=str(company.id) if company else None,
        job_count=len(filtered_jobs),
        jobs=[build_job_link(job) for job in filtered_jobs],
    )


def sort_companies(items: list[CompanySummary], sort_by: str, sort_dir: str) -> list[CompanySummary]:
    reverse = sort_dir == "desc"

    def key(item: CompanySummary) -> object:
        if sort_by == "score":
            return item.score or -1
        if sort_by == "latest_job_at":
            return item.latest_job_at or datetime.min.replace(tzinfo=timezone.utc)
        if sort_by == "avg_applicants":
            return item.avg_applicants if item.avg_applicants is not None else -1
        if sort_by == "company_type":
            return item.company_type or ""
        return item.job_count

    return sorted(items, key=key, reverse=reverse)


async def load_jobs(session: AsyncSession) -> list[Job]:
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.company).selectinload(Company.recruiters))
        .options(selectinload(Job.skills).selectinload(JobSkill.skill))
        .order_by(Job.discovered_at.desc())
        .limit(1000)
    )
    return result.scalars().all()


async def load_recruiters(session: AsyncSession) -> list[Recruiter]:
    result = await session.execute(
        select(Recruiter)
        .options(selectinload(Recruiter.company).selectinload(Company.jobs))
        .order_by(Recruiter.created_at.desc())
    )
    return result.scalars().all()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummary:
    jobs_found = min(await scalar_count(session, select(func.count()).select_from(Job)), 1000)
    saved = await application_count(session, ApplicationStatus.SAVED)
    applied = await application_count(session, ApplicationStatus.APPLIED)
    interviews = await application_count(session, ApplicationStatus.INTERVIEW)
    offers = await application_count(session, ApplicationStatus.OFFER)
    rejected = await application_count(session, ApplicationStatus.REJECTED)

    return DashboardSummary(
        jobs_found=jobs_found,
        saved=saved,
        applied=applied,
        interviews=interviews,
        offers=offers,
        rejected=rejected,
        funnel=[
            FunnelPoint(name="Found", value=jobs_found),
            FunnelPoint(name="Saved", value=saved),
            FunnelPoint(name="Applied", value=applied),
            FunnelPoint(name="Interview", value=interviews),
            FunnelPoint(name="Offer", value=offers),
        ],
    )


@router.get("/jobs", response_model=JobPagination)
async def dashboard_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=MAX_PAGE_SIZE),
    sort_by: str = Query(default="score"),
    sort_dir: str = Query(default="desc"),
    search: str | None = Query(default=None),
    location: str | None = Query(default=None),
    source: list[JobSource] = Query(default_factory=list),
    company_type: list[str] = Query(default_factory=list),
    company: str | None = Query(default=None),
    remote_only: bool | None = Query(default=None),
    min_applicants: int | None = Query(default=None, ge=0),
    max_applicants: int | None = Query(default=None, ge=0),
    skill_weight: float = Query(default=50.0, ge=0.0),
    recency_weight: float = Query(default=30.0, ge=0.0),
    applicant_weight: float = Query(default=20.0, ge=0.0),
    session: AsyncSession = Depends(get_db_session),
) -> JobPagination:
    profile = build_profile()
    weights = {
        "skill": skill_weight,
        "recency": recency_weight,
        "applicants": applicant_weight,
    }
    jobs = await load_jobs(session)
    search_ids = await search_job_ids(search) if search else []
    search_id_order = {job_id: index for index, job_id in enumerate(search_ids)}
    filtered = [
        job
        for job in jobs
        if job_matches_filters(
            job,
            search=search,
            location=location,
            sources=source,
            company_types=company_type,
            company_name_filter=company,
            remote_only=remote_only,
            min_applicants=min_applicants,
            max_applicants=max_applicants,
        )
        and (
            not search_ids
            or str(job.id) in search_id_order
            or normalize_text(search) in normalize_text(" ".join(filter(None, [job.title, canonical_company_name(job), job.location, job.description])))
        )
    ]
    if search_ids:
        filtered.sort(key=lambda job: search_id_order.get(str(job.id), len(search_id_order)))
    scored = [(job, score_job(job, profile, weights)) for job in filtered]
    scored = sort_jobs(scored, sort_by, sort_dir)

    total = len(scored)
    total_pages = ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    end = start + page_size
    page_items = scored[start:end]
    items = [
        build_job_detail(job, profile, rank=index, weights=weights)
        for index, (job, _) in enumerate(page_items, start=start + 1)
    ]
    return JobPagination(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/companies", response_model=CompanyPagination)
async def dashboard_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=MAX_PAGE_SIZE),
    sort_by: str = Query(default="job_count"),
    sort_dir: str = Query(default="desc"),
    search: str | None = Query(default=None),
    location: str | None = Query(default=None),
    company_type: list[str] = Query(default_factory=list),
    source: list[JobSource] = Query(default_factory=list),
    session: AsyncSession = Depends(get_db_session),
) -> CompanyPagination:
    profile = build_profile()
    weights = {"skill": 50.0, "recency": 30.0, "applicants": 20.0}
    jobs = await load_jobs(session)
    filtered_jobs = [
        job
        for job in jobs
        if job_matches_filters(
            job,
            search=search,
            location=location,
            sources=source,
            company_types=company_type,
            company_name_filter=None,
            remote_only=None,
            min_applicants=None,
            max_applicants=None,
        )
    ]
    companies = sort_companies(aggregate_companies(filtered_jobs, profile, weights), sort_by, sort_dir)

    total = len(companies)
    total_pages = ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    end = start + page_size
    page_items = companies[start:end]
    return CompanyPagination(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/recruiters", response_model=RecruiterPagination)
async def dashboard_recruiters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=MAX_PAGE_SIZE),
    search: str | None = Query(default=None),
    location: str | None = Query(default=None),
    source: list[JobSource] = Query(default_factory=list),
    company_type: list[str] = Query(default_factory=list),
    company: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> RecruiterPagination:
    recruiters = await load_recruiters(session)
    filtered = []
    for recruiter in recruiters:
        company_obj = recruiter.company
        company_name = company_obj.name if company_obj else None
        if company and (not company_name or company.lower() not in normalize_text(company_name)):
            continue
        if company_type and (infer_company_type(company_name) or "unknown") not in company_type:
            continue
        if search:
            haystack = normalize_text(
                " ".join(
                    filter(
                        None,
                        [
                            recruiter.full_name,
                            recruiter.title,
                            recruiter.email,
                            recruiter.linkedin_url,
                            recruiter.notes,
                            company_name,
                        ],
                    )
                )
            )
            if normalize_text(search) not in haystack:
                job_haystack = normalize_text(
                    " ".join(job.title for job in (company_obj.jobs if company_obj else []))
                )
                if normalize_text(search) not in job_haystack:
                    continue
        recruiter_detail = build_recruiter_detail(
            recruiter,
            location=location,
            search=search,
            sources=source,
            company_types=company_type,
        )
        if location and recruiter_detail.job_count == 0:
            continue
        if source and recruiter_detail.job_count == 0:
            continue
        filtered.append(recruiter_detail)

    total = len(filtered)
    total_pages = ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]
    return RecruiterPagination(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
