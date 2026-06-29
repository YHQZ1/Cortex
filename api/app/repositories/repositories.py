from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.schemas.repository import RepositorySummary


async def list_repositories(session: AsyncSession) -> list[RepositorySummary]:
    statement = (
        select(
            Repository.source_type,
            Repository.source_ref,
            Repository.name,
            Repository.default_branch,
            Repository.last_indexed_at,
            func.count(func.distinct(SourceFile.id)).label("file_count"),
            func.count(func.distinct(Chunk.id)).label("chunk_count"),
        )
        .outerjoin(SourceFile, SourceFile.repository_id == Repository.id)
        .outerjoin(Chunk, Chunk.repository_id == Repository.id)
        .group_by(Repository.id)
        .order_by(Repository.source_ref.asc())
    )
    rows = (await session.execute(statement)).all()

    return [
        RepositorySummary(
            source_type=row.source_type,
            source_ref=row.source_ref,
            name=row.name,
            default_branch=row.default_branch,
            last_indexed_at=row.last_indexed_at,
            file_count=row.file_count,
            chunk_count=row.chunk_count,
        )
        for row in rows
    ]
