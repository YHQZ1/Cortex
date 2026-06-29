from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.schemas.search import SearchResult, SemanticSearchResult


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
