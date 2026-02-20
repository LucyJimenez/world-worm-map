import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.kobo_ingest import ingest_kobo_submissions

scheduler = BackgroundScheduler(timezone="UTC")
logger = logging.getLogger(__name__)


def run_ingestion_job() -> None:
    db = SessionLocal()
    try:
        result = ingest_kobo_submissions(db, actor="scheduler")
        logger.info("Scheduled Kobo ingestion complete: %s", result)
    except Exception:
        logger.exception("Scheduled Kobo ingestion failed.")
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        run_ingestion_job,
        trigger="cron",
        hour=settings.ingest_hour,
        minute=settings.ingest_minute,
        id="daily_kobo_ingest",
        replace_existing=True,
    )
    scheduler.start()
    job = scheduler.get_job("daily_kobo_ingest")
    logger.info(
        "Kobo scheduler started (UTC %02d:%02d). Next run: %s",
        settings.ingest_hour,
        settings.ingest_minute,
        job.next_run_time.isoformat() if job and job.next_run_time else "unknown",
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
