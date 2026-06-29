import asyncio
from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.db.session import async_session
from app.models.ingestion_job import IngestionSourceType
from app.pipeline.sample_source import get_sample_documents
from app.providers.github import GitHubProvider
from app.repositories.indexed_content import ingest_documents
from app.repositories.ingestion_jobs import (
    get_ingestion_job,
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
    try:
        async with async_session() as session:
            job = await mark_ingestion_job_running(session, job_id)
            if job is None:
                return "missing"
            source_type = job.source_type
            source_ref = job.source_ref or "sample/repository"

        repository_name = source_ref.rsplit("/", 1)[-1]
        default_branch = None
        documents = get_sample_documents()

        if source_type == IngestionSourceType.GITHUB.value and source_ref != "sample/repository":
            fetched_repository = await GitHubProvider(settings).fetch_repository(source_ref)
            source_ref = fetched_repository.source_ref
            repository_name = fetched_repository.name
            default_branch = fetched_repository.default_branch
            documents = fetched_repository.documents

        async with async_session() as session:
            stats = await ingest_documents(
                session,
                ingestion_job_id=job_id,
                source_type=source_type,
                source_ref=source_ref,
                repository_name=repository_name,
                default_branch=default_branch,
                documents=documents,
            )

        async with async_session() as session:
            latest_job = await get_ingestion_job(session, job_id)
            if latest_job is None:
                return "missing"
            await mark_ingestion_job_succeeded(
                session,
                job_id,
                message=(
                    f"Ingested {source_type} source {source_ref}: "
                    f"{stats['indexed_files']} files, "
                    f"{stats['indexed_chunks']} chunks, "
                    f"{stats['skipped_files']} skipped."
                ),
            )
        return "succeeded"
    except Exception as exc:
        async with async_session() as session:
            await mark_ingestion_job_failed(
                session,
                job_id,
                message=f"Ingestion failed: {type(exc).__name__}",
            )
        raise
