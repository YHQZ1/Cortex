from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.schemas.search import SearchResult


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
