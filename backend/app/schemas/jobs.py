from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class JobContact(BaseModel):
    full_name: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    notes: str | None = None


class JobDetail(BaseModel):
    id: str
    rank: int | None = None
    score: int | None = None
    skill_match_score: float | None = None
    recency_score: float | None = None
    applicant_count: int | None = None
    company_type: str | None = None
    company_score: float | None = None
    applicant_score: float | None = None
    source: str
    company: str | None = None
    title: str
    location: str | None = None
    remote: str | None = None
    source_url: str
    matched_keywords: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    tailored_resume: str | None = None
    description: str | None = None
    discovered_at: datetime | None = None
    contacts: list[JobContact] = Field(default_factory=list)


class JobLink(BaseModel):
    id: str
    title: str
    source: str
    source_url: str


class RecruiterDetail(BaseModel):
    id: str
    full_name: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    notes: str | None = None
    company: str | None = None
    company_id: str | None = None
    job_count: int = 0
    jobs: list[JobLink] = Field(default_factory=list)


class RecruiterPagination(BaseModel):
    items: list[RecruiterDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobPagination(BaseModel):
    items: list[JobDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


class CompanySummary(BaseModel):
    company: str
    company_type: str | None = None
    job_count: int
    score: float | None = None
    latest_job_at: datetime | None = None
    avg_applicants: float | None = None
    source_count: int | None = None


class CompanyPagination(BaseModel):
    items: list[CompanySummary]
    total: int
    page: int
    page_size: int
    total_pages: int
