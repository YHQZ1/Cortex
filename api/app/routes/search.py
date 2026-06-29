from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db_session
from app.providers.embeddings import OllamaEmbeddingProvider
from app.providers.vector_store import QdrantVectorStore
from app.repositories.search import (
    get_semantic_search_results,
    keyword_search_chunks,
    merge_search_results,
    search_chunks,
)
from app.schemas.search import SearchRequest, SearchResponse, SemanticSearchResponse

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


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    payload: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticSearchResponse:
    settings = get_settings()
    query_vector = await OllamaEmbeddingProvider(settings).embed_text(payload.query)
    matches = await QdrantVectorStore(settings).search(
        vector=query_vector,
        repository=payload.repository,
        limit=payload.limit,
    )
    results = await get_semantic_search_results(
        session,
        scores_by_chunk_id={match.chunk_id: match.score for match in matches},
    )
    return SemanticSearchResponse(query=payload.query, results=results)


@router.post("/hybrid", response_model=SemanticSearchResponse)
async def hybrid_search(
    payload: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticSearchResponse:
    settings = get_settings()
    retrieval_limit = max(payload.limit * 3, 12)
    query_vector = await OllamaEmbeddingProvider(settings).embed_text(payload.query)
    matches = await QdrantVectorStore(settings).search(
        vector=query_vector,
        repository=payload.repository,
        limit=retrieval_limit,
    )
    semantic_results = await get_semantic_search_results(
        session,
        scores_by_chunk_id={match.chunk_id: match.score for match in matches},
    )
    keyword_results = await keyword_search_chunks(
        session,
        query=payload.query,
        repository=payload.repository,
        limit=retrieval_limit,
    )
    results = merge_search_results(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        limit=payload.limit,
    )
    return SemanticSearchResponse(query=payload.query, results=results)
