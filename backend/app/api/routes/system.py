from fastapi import APIRouter
from worker.tasks import discover_jobs

from backend.app.core.config import get_settings
from backend.app.schemas.profile import JobSearchProfile
from backend.app.schemas.system import ServiceInfo

router = APIRouter()


@router.get("/info", response_model=ServiceInfo)
async def service_info() -> ServiceInfo:
    settings = get_settings()
    return ServiceInfo(name=settings.app_name, environment=settings.app_env, version="0.1.0")


@router.get("/profile", response_model=JobSearchProfile)
async def job_search_profile() -> JobSearchProfile:
    settings = get_settings()
    return JobSearchProfile(
        full_name="Rahul Mathur",
        resume_path=str(settings.profile_resume_path),
        target_job_titles=settings.target_job_titles,
        target_job_locations=settings.target_job_locations,
        target_job_remote_only=settings.target_job_remote_only,
        target_years_experience=settings.target_years_experience,
        target_keywords=settings.target_keywords,
    )


@router.post("/discover")
async def trigger_job_discovery() -> dict[str, str]:
    task = discover_jobs.delay()
    return {"status": "queued", "task_id": task.id}
