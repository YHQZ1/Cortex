from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.schemas.chunk import ChunkPreview


async def get_chunk_preview(session: AsyncSession, chunk_id: UUID) -> ChunkPreview | None:
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
        .where(Chunk.id == chunk_id)
    )
    row = (await session.execute(statement)).one_or_none()
    if row is None:
        return None

    return ChunkPreview(
        chunk_id=row.id,
        repository=row.source_ref,
        path=row.path,
        language=row.language,
        start_line=row.start_line,
        end_line=row.end_line,
        content=row.content,
    )
