from celery import Celery

from backend.app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "job_search_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
