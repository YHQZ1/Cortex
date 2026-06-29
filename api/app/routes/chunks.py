from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.chunks import get_chunk_preview
from app.schemas.chunk import ChunkPreview

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.get("/{chunk_id}", response_model=ChunkPreview)
async def chunk_preview(
    chunk_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ChunkPreview:
    preview = await get_chunk_preview(session, chunk_id)
    if preview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found.",
        )
    return preview
