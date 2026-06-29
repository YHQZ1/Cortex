from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.search import search_chunks
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    results = await search_chunks(
        session,
        query=payload.query,
        repository=payload.repository,
        limit=payload.limit,
    )
    return SearchResponse(query=payload.query, results=results)
