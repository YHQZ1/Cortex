import asyncio
from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.db.session import async_session
from app.models.ingestion_job import IngestionSourceType
from app.pipeline.sample_source import get_sample_documents
from app.providers.github import GitHubFetchDiagnostics, GitHubProvider
from app.repositories.indexed_content import ingest_documents
from app.repositories.ingestion_jobs import (
    get_ingestion_job,
    mark_ingestion_job_failed,
    mark_ingestion_job_running,
    mark_ingestion_job_succeeded,
)
from app.services.vector_indexing import VectorIndexingService

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
        github_diagnostics: GitHubFetchDiagnostics | None = None

        if source_type == IngestionSourceType.GITHUB.value and source_ref != "sample/repository":
            fetched_repository = await GitHubProvider(settings).fetch_repository(source_ref)
            source_ref = fetched_repository.source_ref
            repository_name = fetched_repository.name
            default_branch = fetched_repository.default_branch
            documents = fetched_repository.documents
            github_diagnostics = fetched_repository.diagnostics

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

        vector_count = await VectorIndexingService(settings).index_chunks(stats["chunks"])

        async with async_session() as session:
            latest_job = await get_ingestion_job(session, job_id)
            if latest_job is None:
                return "missing"
            await mark_ingestion_job_succeeded(
                session,
                job_id,
                message=_build_success_message(
                    source_type=source_type,
                    source_ref=source_ref,
                    stats=stats,
                    vector_count=vector_count,
                    github_diagnostics=github_diagnostics,
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


def _build_success_message(
    *,
    source_type: str,
    source_ref: str,
    stats: dict,
    vector_count: int,
    github_diagnostics: GitHubFetchDiagnostics | None,
) -> str:
    parts = [f"Ingested {source_type} source {source_ref}"]

    if github_diagnostics is not None:
        ignored_files = sum(github_diagnostics.ignored_by_reason.values())
        parts.append(
            f"discovered {github_diagnostics.discovered_files} files, "
            f"{github_diagnostics.candidate_files} candidates, "
            f"{ignored_files} ignored"
        )
        reason_summary = _format_reason_counts(github_diagnostics.ignored_by_reason)
        if reason_summary:
            parts.append(f"ignored reasons: {reason_summary}")
        if github_diagnostics.truncated_files:
            parts.append(f"{github_diagnostics.truncated_files} candidates not fetched due to limit")
        if github_diagnostics.fetch_skipped_files:
            parts.append(f"{github_diagnostics.fetch_skipped_files} raw files skipped during fetch")

    parts.append(
        f"indexed {stats['indexed_files']} files, "
        f"{stats['indexed_chunks']} chunks, "
        f"{stats['skipped_files']} post-fetch skipped, "
        f"{vector_count} vectors indexed"
    )
    post_fetch_summary = _format_reason_counts(stats.get("skipped_by_reason", {}))
    if post_fetch_summary:
        parts.append(f"post-fetch skip reasons: {post_fetch_summary}")

    return ". ".join(parts) + "."


def _format_reason_counts(reason_counts: dict[str, int]) -> str:
    return ", ".join(
        f"{count} {reason}" for reason, count in sorted(reason_counts.items())
    )
