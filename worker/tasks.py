import asyncio
import logging

from worker.app import celery_app
from backend.app.services.job_search import build_profile, run_job_discovery

logger = logging.getLogger(__name__)


@celery_app.task(name="jobs.discover")
def discover_jobs() -> dict[str, str | int]:
    profile = build_profile()
    logger.info("Starting job discovery for %s", profile.full_name)
    result = asyncio.run(run_job_discovery(profile))
    logger.info(
        "Discovery complete: %s jobs, %s ranked, report=%s",
        result.discovered_count,
        result.ranked_count,
        result.report_path,
    )
    return {
        "status": "completed",
        "discovered_count": result.discovered_count,
        "ranked_count": result.ranked_count,
        "report_path": str(result.report_path),
    }


@celery_app.task(name="analytics.refresh")
def refresh_analytics() -> dict[str, str]:
    logger.info("Analytics refresh task scheduled for Phase 10 implementation")
    return {"status": "deferred", "phase": "10"}
