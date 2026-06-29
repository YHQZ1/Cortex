import asyncio
from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.db.session import async_session
from app.repositories.ingestion_jobs import (
    mark_ingestion_job_failed,
    mark_ingestion_job_running,
    mark_ingestion_job_succeeded,
)

settings = get_settings()

celery_app = Celery(
    "cortex",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    timezone="UTC",
)


@celery_app.task(name="cortex.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="cortex.process_ingestion_job")
def process_ingestion_job(job_id: str) -> str:
    return asyncio.run(_process_ingestion_job(UUID(job_id)))


async def _process_ingestion_job(job_id: UUID) -> str:
    async with async_session() as session:
        job = await mark_ingestion_job_running(session, job_id)
        if job is None:
            return "missing"

    try:
        # This is the end-to-end placeholder. Real GitHub fetch/chunk/embed work lands here next.
        async with async_session() as session:
            await mark_ingestion_job_succeeded(session, job_id)
        return "succeeded"
    except Exception as exc:
        async with async_session() as session:
            await mark_ingestion_job_failed(
                session,
                job_id,
                message=f"Placeholder ingestion failed: {type(exc).__name__}",
            )
        raise
