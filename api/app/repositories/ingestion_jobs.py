from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_job import IngestionJob, IngestionJobStatus, IngestionSourceType


async def create_ingestion_job(
    session: AsyncSession,
    *,
    source_type: IngestionSourceType,
    source_ref: str | None,
) -> IngestionJob:
    job = IngestionJob(
        source_type=source_type.value,
        source_ref=source_ref,
        status=IngestionJobStatus.PENDING.value,
        message="Queued for ingestion.",
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_ingestion_job(session: AsyncSession, job_id: UUID) -> IngestionJob | None:
    result = await session.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    return result.scalar_one_or_none()


async def mark_ingestion_job_running(session: AsyncSession, job_id: UUID) -> IngestionJob | None:
    job = await get_ingestion_job(session, job_id)
    if job is None:
        return None

    job.status = IngestionJobStatus.RUNNING.value
    job.message = "Ingestion task started."
    job.started_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_ingestion_job_succeeded(
    session: AsyncSession,
    job_id: UUID,
    *,
    message: str = "Ingestion completed.",
) -> IngestionJob | None:
    job = await get_ingestion_job(session, job_id)
    if job is None:
        return None

    job.status = IngestionJobStatus.SUCCEEDED.value
    job.message = message
    job.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_ingestion_job_failed(
    session: AsyncSession,
    job_id: UUID,
    *,
    message: str,
) -> IngestionJob | None:
    job = await get_ingestion_job(session, job_id)
    if job is None:
        return None

    job.status = IngestionJobStatus.FAILED.value
    job.message = message
    job.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(job)
    return job
