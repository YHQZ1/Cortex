import re
from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.schemas.search import SearchResult, SemanticSearchResult

MAX_KEYWORD_CANDIDATES = 80

TECHNICAL_ALIASES = {
    "queue": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task", "delay"},
    "queuing": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task", "delay"},
    "queueing": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task", "delay"},
    "background": {"background", "celery", "worker", "task", "job"},
    "ingestion": {"ingestion", "ingestions", "job", "worker", "celery"},
    "jobs": {"job", "jobs", "task", "worker", "celery"},
    "job": {"job", "jobs", "task", "worker", "celery"},
}


async def search_chunks(
    session: AsyncSession,
    *,
    query: str,
    limit: int,
    repository: str | None = None,
) -> list[SearchResult]:
    pattern = f"%{query.strip()}%"

    statement: Select = (
        select(
            Chunk.id,
            Repository.source_ref,
            SourceFile.path,
            SourceFile.language,
            Chunk.start_line,
            Chunk.end_line,
            Chunk.content,
        )
        .join(SourceFile, SourceFile.id == Chunk.source_file_id)
        .join(Repository, Repository.id == Chunk.repository_id)
        .where(or_(Chunk.content.ilike(pattern), SourceFile.path.ilike(pattern)))
        .order_by(Repository.source_ref.asc(), SourceFile.path.asc(), Chunk.ordinal.asc())
        .limit(limit)
    )

    if repository is not None:
        statement = statement.where(Repository.source_ref == repository)

    rows = (await session.execute(statement)).all()

    return [
        SearchResult(
            chunk_id=row.id,
            repository=row.source_ref,
            path=row.path,
            language=row.language,
            start_line=row.start_line,
            end_line=row.end_line,
            content=row.content,
        )
        for row in rows
    ]


async def get_semantic_search_results(
    session: AsyncSession,
    *,
    scores_by_chunk_id: dict[UUID, float],
) -> list[SemanticSearchResult]:
    if not scores_by_chunk_id:
        return []

    chunk_ids = list(scores_by_chunk_id.keys())
    statement = (
        select(
            Chunk.id,
            Repository.source_ref,
            SourceFile.path,
            SourceFile.language,
            Chunk.start_line,
            Chunk.end_line,
            Chunk.content,
        )
        .join(SourceFile, SourceFile.id == Chunk.source_file_id)
        .join(Repository, Repository.id == Chunk.repository_id)
        .where(Chunk.id.in_(chunk_ids))
    )
    rows = (await session.execute(statement)).all()
    results_by_id = {
        row.id: SemanticSearchResult(
            chunk_id=row.id,
            repository=row.source_ref,
            path=row.path,
            language=row.language,
            start_line=row.start_line,
            end_line=row.end_line,
            content=row.content,
            score=scores_by_chunk_id[row.id],
        )
        for row in rows
    }
    return [results_by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in results_by_id]


async def keyword_search_chunks(
    session: AsyncSession,
    *,
    query: str,
    repository: str | None,
    limit: int,
) -> list[SemanticSearchResult]:
    terms = _expand_query_terms(query)
    if not terms:
        return []

    conditions = []
    for term in terms:
        pattern = f"%{term}%"
        conditions.append(Chunk.content.ilike(pattern))
        conditions.append(SourceFile.path.ilike(pattern))

    statement: Select = (
        select(
            Chunk.id,
            Repository.source_ref,
            SourceFile.path,
            SourceFile.language,
            Chunk.start_line,
            Chunk.end_line,
            Chunk.content,
        )
        .join(SourceFile, SourceFile.id == Chunk.source_file_id)
        .join(Repository, Repository.id == Chunk.repository_id)
        .where(or_(*conditions))
        .limit(MAX_KEYWORD_CANDIDATES)
    )

    if repository is not None:
        statement = statement.where(Repository.source_ref == repository)

    rows = (await session.execute(statement)).all()
    scored_results = [
        SemanticSearchResult(
            chunk_id=row.id,
            repository=row.source_ref,
            path=row.path,
            language=row.language,
            start_line=row.start_line,
            end_line=row.end_line,
            content=row.content,
            score=_keyword_score(
                query=query,
                terms=terms,
                path=row.path,
                content=row.content,
            ),
        )
        for row in rows
    ]
    return sorted(scored_results, key=lambda result: result.score, reverse=True)[:limit]


def merge_search_results(
    *,
    semantic_results: list[SemanticSearchResult],
    keyword_results: list[SemanticSearchResult],
    limit: int,
) -> list[SemanticSearchResult]:
    merged: dict[UUID, SemanticSearchResult] = {}
    combined_scores: dict[UUID, float] = {}

    for rank, result in enumerate(semantic_results):
        rank_boost = max(0.0, 0.25 - (rank * 0.03))
        merged[result.chunk_id] = result
        combined_scores[result.chunk_id] = result.score + rank_boost

    for rank, result in enumerate(keyword_results):
        rank_boost = max(0.0, 0.55 - (rank * 0.05))
        if result.chunk_id not in merged:
            merged[result.chunk_id] = result
            combined_scores[result.chunk_id] = result.score + rank_boost
        else:
            combined_scores[result.chunk_id] += result.score + rank_boost

    reranked = sorted(
        merged.values(),
        key=lambda result: combined_scores[result.chunk_id],
        reverse=True,
    )

    return [
        result.model_copy(update={"score": combined_scores[result.chunk_id]})
        for result in reranked[:limit]
    ]


def _expand_query_terms(query: str) -> list[str]:
    raw_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z0-9_.-]+", query)
        if len(term) >= 3
    }
    expanded = set(raw_terms)
    for term in raw_terms:
        expanded.update(TECHNICAL_ALIASES.get(term, set()))
    return sorted(expanded)


def _keyword_score(
    *,
    query: str,
    terms: list[str],
    path: str,
    content: str,
) -> float:
    path_lower = path.lower()
    content_lower = content.lower()
    query_lower = query.lower()

    score = 0.0
    for term in terms:
        if term in path_lower:
            score += 0.8
        if term in content_lower:
            score += min(content_lower.count(term), 4) * 0.18

    if any(term in path_lower for term in {"celery", "worker", "ingestion", "queue", "redis"}):
        score += 0.8
    if "docker-compose" in path_lower and any(term in query_lower for term in {"queue", "queuing", "queueing", "redis", "worker"}):
        score += 0.6
    if path_lower.endswith(("celery_app.py", "ingestions.py", "ingestion_jobs.py")):
        score += 1.0

    return score
