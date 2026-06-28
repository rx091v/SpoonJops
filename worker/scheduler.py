import logging
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.core.logging import configure_logging
from worker.tasks import discover_jobs, refresh_analytics

logger = logging.getLogger(__name__)
shutdown_requested = False


def request_shutdown(_: int, __: object) -> None:
    global shutdown_requested
    shutdown_requested = True


def main() -> None:
    configure_logging()
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(discover_jobs.delay, "cron", hour=1, minute=0, id="daily_job_search")
    scheduler.add_job(refresh_analytics.delay, "cron", hour=2, minute=0, id="daily_analytics")
    scheduler.start()
    logger.info("Scheduler started")

    while not shutdown_requested:
        time.sleep(1)

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
