from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.ingestion_jobs import create_ingestion_job, get_ingestion_job
from app.schemas.ingestion import IngestionJobCreate, IngestionJobRead
from app.workers.celery_app import process_ingestion_job

router = APIRouter(prefix="/ingestions", tags=["ingestions"])


@router.post("", response_model=IngestionJobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_ingestion(
    payload: IngestionJobCreate,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobRead:
    job = await create_ingestion_job(
        session,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
    )

    try:
        process_ingestion_job.delay(str(job.id))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to enqueue ingestion job: {type(exc).__name__}",
        ) from exc

    return IngestionJobRead.model_validate(job)


@router.get("/{job_id}", response_model=IngestionJobRead)
async def get_ingestion(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobRead:
    job = await get_ingestion_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found.")

    return IngestionJobRead.model_validate(job)
