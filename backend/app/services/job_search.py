from __future__ import annotations

import asyncio
import json
import logging
import re
import textwrap
from collections.abc import AsyncIterator, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlsplit, urlunsplit

import httpx
from openpyxl import Workbook
from openpyxl.styles import Font
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings, get_settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models import Company, Job, Recruiter
from browser.session import persistent_browser_context
from shared.constants import JobSource
from backend.app.services.search_index import index_job_documents

logger = logging.getLogger(__name__)
MAX_DISCOVERED_JOBS = 1000


@dataclass(frozen=True)
class SearchProfile:
    full_name: str
    resume_path: Path
    target_job_titles: list[str]
    target_job_locations: list[str]
    target_job_remote_only: bool
    target_years_experience: int
    target_keywords: list[str]
    lever_boards: list[str]
    greenhouse_boards: list[str]
    ashby_boards: list[str]


@dataclass(frozen=True)
class DiscoveredJob:
    source: JobSource
    title: str
    company_name: str | None
    location: str | None
    remote_type: str | None
    source_url: str
    external_id: str | None = None
    description: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    posted_at: datetime | None = None
    applicant_count: int | None = None
    matched_keywords: list[str] = field(default_factory=list)
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    contacts: list["DiscoveredContact"] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveredContact:
    full_name: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class RankedJob:
    job: DiscoveredJob
    score: int
    reasons: list[str]
    matched_keywords: list[str]


def build_profile(settings: Settings | None = None) -> SearchProfile:
    settings = settings or get_settings()
    return SearchProfile(
        full_name="Rahul Mathur",
        resume_path=settings.profile_resume_path,
        target_job_titles=settings.target_job_titles,
        target_job_locations=settings.target_job_locations,
        target_job_remote_only=settings.target_job_remote_only,
        target_years_experience=settings.target_years_experience,
        target_keywords=settings.target_keywords,
        lever_boards=settings.lever_boards,
        greenhouse_boards=settings.greenhouse_boards,
        ashby_boards=settings.ashby_boards,
    )


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip().lower()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "job"


def canonicalize_source_url(url: str | None) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def extract_applicant_count(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(\d{1,4})\s+(?:applicants?|candidates?)\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def score_job(profile: SearchProfile, job: DiscoveredJob) -> RankedJob:
    haystack = " ".join(
        filter(None, [job.title, job.company_name, job.location, job.remote_type, job.description])
    )
    haystack_normalized = normalize_text(haystack)
    reasons: list[str] = []
    matched_keywords: list[str] = []
    score = 0

    for title in profile.target_job_titles:
        if normalize_text(title) in normalize_text(job.title):
            score += 30
            reasons.append(f"title matches {title}")

    for location in profile.target_job_locations:
        if normalize_text(location) in haystack_normalized:
            score += 15
            reasons.append(f"location mentions {location}")

    if profile.target_job_remote_only and "remote" in haystack_normalized:
        score += 15
        reasons.append("remote-friendly")
    elif not profile.target_job_remote_only and "remote" in haystack_normalized:
        score += 8
        reasons.append("remote-friendly")

    for keyword in profile.target_keywords:
        if normalize_text(keyword) in haystack_normalized:
            matched_keywords.append(keyword)
            score += 10

    if profile.target_years_experience >= 10:
        if any(token in haystack_normalized for token in ["staff", "lead", "principal", "senior"]):
            score += 10
            reasons.append("seniority fit")

    if "java" in haystack_normalized or "spring boot" in haystack_normalized:
        score += 10
        reasons.append("backend stack fit")

    if "kubernetes" in haystack_normalized or "cloud" in haystack_normalized:
        score += 8
        reasons.append("platform/cloud fit")

    if job.description:
        desc = normalize_text(job.description)
        for keyword in profile.target_keywords:
            if normalize_text(keyword) in desc and keyword not in matched_keywords:
                matched_keywords.append(keyword)

    score = min(score, 100)
    return RankedJob(job=job, score=score, reasons=reasons, matched_keywords=matched_keywords)


async def fetch_json(client: httpx.AsyncClient, method: str, url: str, *, json_body: dict | None = None) -> dict | list:
    response = await client.request(method, url, json=json_body)
    response.raise_for_status()
    return response.json()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def clean_description(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()


def extract_contacts_from_text(text: str | None, *, source_url: str, source_name: str | None = None) -> list[DiscoveredContact]:
    if not text:
        return []

    contact_candidates: list[DiscoveredContact] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    blocked_email_markers = {"sentry.io", "instahyre.com", "linkedin.com"}
    blocked_name_tokens = {
        "find",
        "jobs",
        "company",
        "profile",
        "help",
        "center",
        "post",
        "your",
        "success",
        "stories",
        "product",
        "academy",
        "software",
        "engineering",
        "marketing",
        "sales",
        "internship",
        "recruiter",
        "hr",
        "talent",
        "acquisition",
        "technical",
        "interview",
        "prep",
        "customer",
        "care",
        "partner",
        "associate",
        "senior",
        "principal",
        "lead",
    }

    email_pattern = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    linkedin_pattern = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[^\\s\"'<>]+", re.IGNORECASE)
    title_pattern = re.compile(
        r"(?i)(recruiter|talent acquisition|hiring manager|hr|people partner|sourcer|people ops|people operations)"
    )
    name_pattern = re.compile(
        r"\b([A-Z][a-zA-Z.'-]+(?:\s+[A-Z][a-zA-Z.'-]+){1,3})\b"
    )

    for email in email_pattern.findall(text):
        if any(marker in email.lower() for marker in blocked_email_markers):
            continue
        key = (None, email.lower(), None)
        if key in seen:
            continue
        seen.add(key)
        contact_candidates.append(
            DiscoveredContact(
                full_name=email,
                email=email,
                notes=f"Extracted from {source_name or 'source'} page: {source_url}",
            )
        )

    for linkedin_url in linkedin_pattern.findall(text):
        key = (None, None, linkedin_url.lower())
        if key in seen:
            continue
        seen.add(key)
        contact_candidates.append(
            DiscoveredContact(
                full_name=linkedin_url.rsplit("/", 1)[-1].replace("-", " ").title(),
                linkedin_url=linkedin_url,
                notes=f"LinkedIn profile reference from {source_name or 'source'} page: {source_url}",
            )
        )

    for raw_line in re.split(r"[\r\n]+", text):
        line = re.sub(r"\s+", " ", raw_line).strip(" \t-•")
        if not line:
            continue
        if not any(separator in line for separator in [" - ", " | ", ":"]):
            continue
        split_match = re.match(r"^(?P<left>.+?)\s*[-|:]\s*(?P<right>.+)$", line)
        if not split_match:
            continue
        left = split_match.group("left").strip()
        right = split_match.group("right").strip()
        left_tokens = {token.lower() for token in re.findall(r"[A-Za-z]+", left)}
        right_tokens = {token.lower() for token in re.findall(r"[A-Za-z]+", right)}
        left_name = name_pattern.search(left)
        right_name = name_pattern.search(right)
        left_is_person = bool(left_name) and not (left_tokens & blocked_name_tokens)
        right_is_person = bool(right_name) and not (right_tokens & blocked_name_tokens)
        if title_pattern.search(left) and right_is_person:
            name = right_name.group(1).strip()
            title = left
        elif title_pattern.search(right) and left_is_person:
            name = left_name.group(1).strip()
            title = right
        else:
            continue
        key = (name.lower(), None, None)
        if key in seen:
            continue
        seen.add(key)
        contact_candidates.append(
            DiscoveredContact(
                full_name=name,
                title=title.title() if title else None,
                notes=f"Contact-like line from {source_name or 'source'} page: {source_url}",
            )
        )

    return contact_candidates


def build_query_variants(profile: SearchProfile) -> list[tuple[str, str]]:
    variants: list[tuple[str, str]] = []
    for title in profile.target_job_titles:
        for location in profile.target_job_locations:
            variants.append((title, location))
    return variants


def listing_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def parse_linkedin_listing_text(text: str | None) -> tuple[str | None, str | None, str | None]:
    lines = listing_lines(text)
    title = lines[0] if lines else None
    company = lines[2] if len(lines) > 2 else None
    location = lines[3] if len(lines) > 3 else None
    return title, company, location


def parse_instahyre_listing_text(text: str | None) -> tuple[str | None, str | None, str | None]:
    lines = listing_lines(text)
    if not lines:
        return None, None, None
    first = lines[0]
    if " - " in first:
        company, title = first.split(" - ", 1)
    else:
        company, title = None, first
    location = next((line for line in lines if line.startswith("Job available in ")), None)
    if location:
        location = location.replace("Job available in ", "").strip()
    return title or None, company or None, location


async def discover_lever_jobs(client: httpx.AsyncClient, profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    for board in profile.lever_boards:
        url = f"https://api.lever.co/v0/postings/{board}?mode=json"
        try:
            payload = await fetch_json(client, "GET", url)
        except httpx.HTTPError as exc:
            logger.warning("lever fetch failed for %s: %s", board, exc)
            continue
        for item in payload if isinstance(payload, list) else []:
            description = clean_description(item.get("description"))
            source_url = canonicalize_source_url(item.get("hostedUrl") or item.get("applyUrl") or url)
            discovered.append(
                DiscoveredJob(
                    source=JobSource.LEVER,
                    title=item.get("text") or item.get("title") or "Unknown title",
                    company_name=item.get("categories", {}).get("team") or board,
                    location=item.get("categories", {}).get("location"),
                    remote_type=item.get("categories", {}).get("commitment"),
                    source_url=source_url,
                    external_id=item.get("id"),
                    description=description,
                    posted_at=parse_datetime(item.get("createdAt")),
                    applicant_count=extract_applicant_count(description),
                    contacts=extract_contacts_from_text(description, source_url=source_url, source_name="lever"),
                )
            )
    return discovered


async def discover_greenhouse_jobs(client: httpx.AsyncClient, profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    for board in profile.greenhouse_boards:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        try:
            payload = await fetch_json(client, "GET", url)
        except httpx.HTTPError as exc:
            logger.warning("greenhouse fetch failed for %s: %s", board, exc)
            continue
        for item in payload.get("jobs", []):
            description = clean_description(item.get("content"))
            source_url = canonicalize_source_url(item.get("absolute_url") or url)
            discovered.append(
                DiscoveredJob(
                    source=JobSource.GREENHOUSE,
                    title=item.get("title") or "Unknown title",
                    company_name=board,
                    location=(item.get("location") or {}).get("name"),
                    remote_type=None,
                    source_url=source_url,
                    external_id=str(item.get("id")) if item.get("id") is not None else None,
                    description=description,
                    posted_at=parse_datetime(item.get("updated_at")),
                    applicant_count=extract_applicant_count(description),
                    contacts=extract_contacts_from_text(description, source_url=source_url, source_name="greenhouse"),
                )
            )
    return discovered


async def discover_ashby_jobs(client: httpx.AsyncClient, profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    url = "https://api.ashbyhq.com/job.list"
    for board in profile.ashby_boards:
        try:
            payload = await fetch_json(
                client,
                "POST",
                url,
                json_body={"status": ["Open"], "title": None, "limit": 200, "companyId": board},
            )
        except httpx.HTTPError as exc:
            logger.warning("ashby fetch failed for %s: %s", board, exc)
            continue
        for item in payload.get("jobs", []):
            job_url = item.get("jobUrl") or item.get("jobPostingUrl") or url
            job_url = canonicalize_source_url(job_url)
            description = clean_description(item.get("descriptionHtml") or item.get("description"))
            discovered.append(
                DiscoveredJob(
                    source=JobSource.ASHBY,
                    title=item.get("title") or "Unknown title",
                    company_name=board,
                    location=(item.get("location") or {}).get("name") if isinstance(item.get("location"), dict) else item.get("location"),
                    remote_type="remote" if item.get("isRemote") else None,
                    source_url=job_url,
                    external_id=item.get("id"),
                    description=description,
                    posted_at=parse_datetime(item.get("publishedAt") or item.get("updatedAt")),
                    applicant_count=extract_applicant_count(description),
                    contacts=extract_contacts_from_text(description, source_url=job_url, source_name="ashby"),
                )
            )
    return discovered


async def discover_browser_jobs(profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    search_pages = [
        JobSource.LINKEDIN,
        JobSource.INSTAHYRE,
    ]
    logger.info("Starting browser discovery for %s sources", len(search_pages))
    async with persistent_browser_context(Path("/app/storage/browser"), headless=True) as context:
        for source in search_pages:
            if source == JobSource.LINKEDIN:
                discovered.extend(await discover_linkedin_jobs(context, profile))
            elif source == JobSource.INSTAHYRE:
                discovered.extend(await discover_instahyre_jobs(context, profile))
    logger.info("Browser discovery yielded %s jobs", len(discovered))
    return discovered


async def discover_linkedin_jobs(context, profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    for title, location in build_query_variants(profile):
        url = (
            "https://www.linkedin.com/jobs/search/?"
            f"keywords={quote_plus(title)}&location={quote_plus(location)}&f_TPR=r604800&sortBy=R"
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(4000)
            link_data = await page.eval_on_selector_all(
                'a',
                """
                els => els
                  .map(a => ({href: a.href || '', text: (a.innerText || a.textContent || '').trim()}))
                  .filter(item => item.href.includes('/jobs/view/'))
                """,
            )
            for item in link_data[:25]:
                link = item.get("href")
                if not link:
                    continue
                link = canonicalize_source_url(link)
                subpage = await context.new_page()
                body = item.get("text") or ""
                heading = None
                listing_title, company_name, listing_location = parse_linkedin_listing_text(item.get("text"))
                try:
                    await subpage.goto(link, wait_until="domcontentloaded", timeout=20000)
                    await subpage.wait_for_timeout(2500)
                    try:
                        heading = await subpage.locator("h1").first.text_content(timeout=5000)
                    except Exception:
                        heading = None
                    try:
                        body = await subpage.locator("body").inner_text(timeout=10000)
                    except Exception:
                        body = item.get("text") or ""
                    contacts = extract_contacts_from_text(
                        body,
                        source_url=link,
                        source_name="linkedin",
                    )
                    title_text = heading or listing_title or title
                    discovered.append(
                        DiscoveredJob(
                            source=JobSource.LINKEDIN,
                            title=title_text.strip() if title_text else "Unknown title",
                            company_name=company_name,
                            location=listing_location or location,
                            remote_type="remote" if "remote" in normalize_text(body) else None,
                            source_url=link,
                            description=body[:8000],
                            applicant_count=extract_applicant_count(body),
                            contacts=contacts,
                        )
                    )
                finally:
                    await subpage.close()
        except Exception as exc:  # pragma: no cover - browser dependent
            logger.warning("linkedin discovery failed for %s/%s: %s", title, location, exc)
        finally:
            await page.close()
    return dedupe_jobs(discovered)


async def discover_instahyre_jobs(context, profile: SearchProfile) -> list[DiscoveredJob]:
    discovered: list[DiscoveredJob] = []
    seed_urls = [
        "https://www.instahyre.com/search-jobs/",
        "https://www.instahyre.com/jobs-in-bangalore/",
        "https://www.instahyre.com/jobs-in-remote/",
    ]
    for seed_url in seed_urls:
        page = await context.new_page()
        try:
            await page.goto(seed_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(4000)
            link_data = await page.eval_on_selector_all(
                'a[href*="/job-"]',
                """
                els => els.map(a => ({
                    href: a.href || '',
                    text: (a.innerText || a.textContent || '').trim(),
                })).filter(item => item.href.includes('/job-'))
                """,
            )
            links = [item["href"] for item in link_data if item.get("href")]
            for item in link_data[:25]:
                link = item.get("href")
                if not link:
                    continue
                link = canonicalize_source_url(link)
                subpage = await context.new_page()
                try:
                    await subpage.goto(link, wait_until="domcontentloaded", timeout=20000)
                    heading = await subpage.locator("h1").first.text_content()
                    body = await subpage.locator("body").inner_text()
                    contacts = extract_contacts_from_text(
                        body,
                        source_url=link,
                        source_name="instahyre",
                    )
                    listing_title, company_name, listing_location = parse_instahyre_listing_text(item.get("text"))
                    discovered.append(
                        DiscoveredJob(
                            source=JobSource.INSTAHYRE,
                            title=((heading or listing_title or "Unknown title").strip()),
                            company_name=company_name,
                            location=listing_location or ("Bengaluru" if "bangalore" in normalize_text(body) else None),
                            remote_type="remote" if "remote" in normalize_text(body) else None,
                            source_url=link,
                            description=body[:8000],
                            applicant_count=extract_applicant_count(body),
                            contacts=contacts,
                        )
                    )
                finally:
                    await subpage.close()
        except Exception as exc:  # pragma: no cover - browser dependent
            logger.warning("instahyre discovery failed for %s: %s", seed_url, exc)
        finally:
            await page.close()
    return dedupe_jobs(discovered)


def dedupe_jobs(jobs: Sequence[DiscoveredJob]) -> list[DiscoveredJob]:
    seen: set[tuple[JobSource, str]] = set()
    deduped: list[DiscoveredJob] = []
    for job in jobs:
        key = (job.source, canonicalize_source_url(job.source_url))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped


async def discover_all_jobs(profile: SearchProfile) -> list[DiscoveredJob]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        public_jobs = await asyncio.gather(
            discover_lever_jobs(client, profile),
            discover_greenhouse_jobs(client, profile),
            discover_ashby_jobs(client, profile),
            discover_browser_jobs(profile),
        )
    jobs = [job for batch in public_jobs for job in batch]
    return dedupe_jobs(jobs)[:MAX_DISCOVERED_JOBS]


async def upsert_jobs(session: AsyncSession, jobs: Sequence[DiscoveredJob]) -> list[Job]:
    persisted: list[Job] = []
    for discovered in jobs:
        company = None
        if discovered.company_name:
            result = await session.execute(select(Company).where(Company.name == discovered.company_name))
            company = result.scalar_one_or_none()
            if company is None:
                company = Company(name=discovered.company_name)
                session.add(company)
                await session.flush()

        result = await session.execute(
            select(Job).where(Job.source == discovered.source, Job.source_url == discovered.source_url)
        )
        job = result.scalar_one_or_none()
        if job is None:
            job = Job(
                company_id=company.id if company else None,
                title=discovered.title,
                source=discovered.source,
                source_url=discovered.source_url,
                external_id=discovered.external_id,
                location=discovered.location,
                remote_type=discovered.remote_type,
                description=discovered.description,
                salary_min=discovered.salary_min,
                salary_max=discovered.salary_max,
                posted_at=discovered.posted_at,
                is_active=True,
            )
            session.add(job)
        else:
            job.company_id = company.id if company else job.company_id
            job.title = discovered.title
            job.external_id = discovered.external_id
            job.location = discovered.location
            job.remote_type = discovered.remote_type
            job.description = discovered.description
            job.salary_min = discovered.salary_min
            job.salary_max = discovered.salary_max
            job.posted_at = discovered.posted_at
            job.is_active = True
        persisted.append(job)
    await session.flush()
    return persisted


async def upsert_recruiters(session: AsyncSession, jobs: Sequence[DiscoveredJob]) -> None:
    for discovered in jobs:
        if not discovered.company_name or not discovered.contacts:
            continue

        company_result = await session.execute(select(Company).where(Company.name == discovered.company_name))
        company = company_result.scalar_one_or_none()
        if company is None:
            continue

        for contact in discovered.contacts:
            full_name = contact.full_name.strip() if contact.full_name else ""
            if not full_name:
                continue

            matcher = select(Recruiter).where(Recruiter.company_id == company.id)
            if contact.email:
                matcher = matcher.where(Recruiter.email == contact.email)
            elif contact.linkedin_url:
                matcher = matcher.where(Recruiter.linkedin_url == contact.linkedin_url)
            else:
                matcher = matcher.where(Recruiter.full_name == full_name)

            result = await session.execute(matcher)
            recruiter = result.scalar_one_or_none()
            if recruiter is None:
                recruiter = Recruiter(
                    company_id=company.id,
                    full_name=full_name,
                    title=contact.title,
                    email=contact.email,
                    linkedin_url=contact.linkedin_url,
                    notes=contact.notes or f"Discovered from {discovered.source.value}: {discovered.source_url}",
                )
                session.add(recruiter)
            else:
                recruiter.title = recruiter.title or contact.title
                recruiter.email = recruiter.email or contact.email
                recruiter.linkedin_url = recruiter.linkedin_url or contact.linkedin_url
                recruiter.notes = recruiter.notes or contact.notes or f"Discovered from {discovered.source.value}: {discovered.source_url}"


def create_cover_page_pdf(profile: SearchProfile, ranked_job: RankedJob, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_pdf = output_path.with_suffix(".cover.pdf")
    canv = canvas.Canvas(str(temp_pdf), pagesize=letter)
    width, height = letter
    left = 54
    y = height - 54

    lines = [
        f"Tailored application for {ranked_job.job.title}",
        f"Company: {ranked_job.job.company_name or 'Unknown'}",
        f"Source: {ranked_job.job.source.value}",
        f"Score: {ranked_job.score}/100",
        "",
        "Matched keywords:",
        ", ".join(ranked_job.matched_keywords) if ranked_job.matched_keywords else "None detected",
        "",
        "Why this is a fit:",
    ] + [f"- {reason}" for reason in ranked_job.reasons[:8]]

    canv.setFont("Helvetica-Bold", 16)
    canv.drawString(left, y, profile.full_name)
    y -= 24
    canv.setFont("Helvetica", 11)
    for line in lines:
        wrapped = textwrap.wrap(line, width=90) or [""]
        for part in wrapped:
            if y < 72:
                canv.showPage()
                y = height - 54
                canv.setFont("Helvetica", 11)
            canv.drawString(left, y, part)
            y -= 15
        y -= 2
    canv.save()
    writer = PdfWriter()
    for pdf_path in [temp_pdf, profile.resume_path]:
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            writer.add_page(page)
    with output_path.open("wb") as handle:
        writer.write(handle)
    temp_pdf.unlink(missing_ok=True)
    return output_path


def write_excel_report(profile: SearchProfile, ranked_jobs: Sequence[RankedJob], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"job_search_{date.today().isoformat()}.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Ranked Jobs"

    headers = [
        "Rank",
        "Score",
        "Source",
        "Company",
        "Title",
        "Location",
        "Remote",
        "URL",
        "Matched Keywords",
        "Reasons",
        "HR Contacts",
        "Tailored Resume",
    ]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for index, ranked in enumerate(sorted(ranked_jobs, key=lambda item: item.score, reverse=True), start=1):
        bundle_slug = slugify(f"{ranked.job.company_name or 'unknown'}-{ranked.job.title}")
        tailored_resume = output_dir / "tailored_resumes" / f"{bundle_slug}.pdf"
        sheet.append(
            [
                index,
                ranked.score,
                ranked.job.source.value,
                ranked.job.company_name or "",
                ranked.job.title,
                ranked.job.location or "",
                ranked.job.remote_type or "",
                ranked.job.source_url,
                ", ".join(ranked.matched_keywords),
                " | ".join(ranked.reasons),
                " | ".join(
                    filter(
                        None,
                        [
                            f"{contact.full_name}{f' ({contact.title})' if contact.title else ''}"
                            for contact in ranked.job.contacts
                        ],
                    )
                ),
                str(tailored_resume),
            ]
        )

    workbook.save(report_path)
    return report_path


def create_application_bundle(profile: SearchProfile, ranked_job: RankedJob, output_dir: Path) -> Path:
    bundle_slug = slugify(f"{ranked_job.job.company_name or 'unknown'}-{ranked_job.job.title}")
    bundle_dir = output_dir / bundle_slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    cover_pdf = bundle_dir / f"{bundle_slug}.pdf"
    create_cover_page_pdf(profile, ranked_job, cover_pdf)

    cover_letter = bundle_dir / "cover_letter.md"
    cover_letter.write_text(
        "\n".join(
            [
                f"# Cover Letter for {ranked_job.job.title}",
                "",
                f"Target: {profile.full_name}",
                f"Company: {ranked_job.job.company_name or 'Unknown'}",
                f"Score: {ranked_job.score}/100",
                "",
                "This application bundle was generated by the discovery agent.",
                "",
                "Matched keywords:",
                ", ".join(ranked_job.matched_keywords) if ranked_job.matched_keywords else "None",
                "",
                "Reasons:",
                *[f"- {reason}" for reason in ranked_job.reasons],
            ]
        ),
        encoding="utf-8",
    )

    manifest = bundle_dir / "bundle.json"
    manifest.write_text(
        json.dumps(
            {
                "company": ranked_job.job.company_name,
                "title": ranked_job.job.title,
                "source": ranked_job.job.source.value,
                "url": ranked_job.job.source_url,
                "score": ranked_job.score,
                "matched_keywords": ranked_job.matched_keywords,
                "reasons": ranked_job.reasons,
                "contacts": [asdict(contact) for contact in ranked_job.job.contacts],
                "resume_pdf": str(cover_pdf),
                "cover_letter": str(cover_letter),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return bundle_dir


@dataclass(frozen=True)
class JobDiscoveryRun:
    discovered_count: int
    ranked_count: int
    report_path: Path
    top_bundles: list[Path]


async def run_job_discovery(profile: SearchProfile | None = None) -> JobDiscoveryRun:
    profile = profile or build_profile()
    discovered = await discover_all_jobs(profile)
    ranked = [score_job(profile, job) for job in discovered]

    async with AsyncSessionLocal() as session:
        persisted_jobs = await upsert_jobs(session, discovered)
        await upsert_recruiters(session, discovered)
        await session.commit()

    await index_job_documents(
        [
            {
                "job_id": str(job.id),
                "title": job.title,
                "company": discovered_item.company_name or "",
                "location": discovered_item.location or "",
                "remote_type": discovered_item.remote_type or "",
                "source": discovered_item.source.value,
                "source_url": discovered_item.source_url,
                "description": discovered_item.description or "",
                "matched_keywords": discovered_item.matched_keywords,
            }
            for job, discovered_item in zip(persisted_jobs, discovered, strict=False)
            if getattr(job, "id", None)
        ]
    )

    reports_dir = Path("/app/storage/reports")
    bundles_dir = Path("/app/storage/application_bundles")
    report_path = write_excel_report(profile, ranked, reports_dir)
    top_bundles: list[Path] = []
    for ranked_job in sorted(ranked, key=lambda item: item.score, reverse=True)[:10]:
        top_bundles.append(create_application_bundle(profile, ranked_job, bundles_dir))

    return JobDiscoveryRun(
        discovered_count=len(discovered),
        ranked_count=len(ranked),
        report_path=report_path,
        top_bundles=top_bundles,
    )
