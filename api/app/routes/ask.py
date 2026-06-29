from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db_session
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag import RagService

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AskResponse:
    return await RagService(get_settings()).answer(
        session,
        question=payload.question,
        repository=payload.repository,
        limit=payload.limit,
    )


@router.post("/stream")
async def ask_stream(
    payload: AskRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    return StreamingResponse(
        RagService(get_settings()).answer_stream(
            session,
            question=payload.question,
            repository=payload.repository,
            limit=payload.limit,
        ),
        media_type="application/x-ndjson",
    )
