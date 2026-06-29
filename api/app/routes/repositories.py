from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db_session
from app.models.ingestion_job import IngestionSourceType
from app.providers.vector_store import QdrantVectorStore
from app.repositories.ingestion_jobs import create_ingestion_job
from app.repositories.repositories import (
    delete_repository_by_source_ref,
    get_repository_by_source_ref,
    list_repositories,
)
from app.schemas.ingestion import IngestionJobRead
from app.schemas.repository import RepositorySummary
from app.workers.celery_app import process_ingestion_job

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositorySummary])
async def repositories(
    session: AsyncSession = Depends(get_db_session),
) -> list[RepositorySummary]:
    return await list_repositories(session)


@router.post(
    "/{source_ref:path}/reindex",
    response_model=IngestionJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reindex_repository(
    source_ref: str,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobRead:
    repository = await get_repository_by_source_ref(session, source_ref)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    job = await create_ingestion_job(
        session,
        source_type=IngestionSourceType.GITHUB,
        source_ref=repository.source_ref,
    )
    try:
        process_ingestion_job.delay(str(job.id))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to enqueue ingestion job: {type(exc).__name__}",
        ) from exc

    return IngestionJobRead.model_validate(job)


@router.delete("/{source_ref:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    source_ref: str,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    repository = await delete_repository_by_source_ref(session, source_ref)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    await QdrantVectorStore(get_settings()).delete_repository(repository.id)
