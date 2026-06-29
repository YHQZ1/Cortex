from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.repositories import list_repositories
from app.schemas.repository import RepositorySummary

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositorySummary])
async def repositories(
    session: AsyncSession = Depends(get_db_session),
) -> list[RepositorySummary]:
    return await list_repositories(session)
