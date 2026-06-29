import json
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.providers.embeddings import OllamaEmbeddingProvider
from app.providers.llm import OllamaLLMProvider
from app.providers.vector_store import QdrantVectorStore
from app.repositories.search import (
    get_semantic_search_results,
    keyword_search_chunks,
    merge_search_results,
)
from app.schemas.ask import AskResponse, AskSource


class RagService:
    def __init__(self, settings: Settings) -> None:
        self._embeddings = OllamaEmbeddingProvider(settings)
        self._llm = OllamaLLMProvider(settings)
        self._vector_store = QdrantVectorStore(settings)

    async def answer(
        self,
        session: AsyncSession,
        *,
        question: str,
        repository: str | None,
        limit: int,
    ) -> AskResponse:
        chunks = await self._retrieve_chunks(
            session,
            question=question,
            repository=repository,
            limit=limit,
        )

        if not chunks:
            return AskResponse(
                question=question,
                answer="I could not find relevant indexed context for that question.",
                sources=[],
            )

        answer = await self._llm.generate_answer(
            question=question,
            context=_format_context(chunks),
        )
        return AskResponse(
            question=question,
            answer=answer,
            sources=[
                _to_ask_source(chunk) for chunk in chunks
            ],
        )

    async def answer_stream(
        self,
        session: AsyncSession,
        *,
        question: str,
        repository: str | None,
        limit: int,
    ) -> AsyncIterator[str]:
        chunks = await self._retrieve_chunks(
            session,
            question=question,
            repository=repository,
            limit=limit,
        )
        sources = [_to_ask_source(chunk) for chunk in chunks]

        yield _stream_event("sources", sources=[source.model_dump(mode="json") for source in sources])

        if not chunks:
            yield _stream_event(
                "token",
                content="I could not find relevant indexed context for that question.",
            )
            yield _stream_event("done")
            return

        async for token in self._llm.stream_answer(
            question=question,
            context=_format_context(chunks),
        ):
            yield _stream_event("token", content=token)

        yield _stream_event("done")

    async def _retrieve_chunks(
        self,
        session: AsyncSession,
        *,
        question: str,
        repository: str | None,
        limit: int,
    ) -> list:
        retrieval_limit = max(limit * 3, 12)
        query_vector = await self._embeddings.embed_text(question)
        matches = await self._vector_store.search(
            vector=query_vector,
            repository=repository,
            limit=retrieval_limit,
        )
        semantic_chunks = await get_semantic_search_results(
            session,
            scores_by_chunk_id={match.chunk_id: match.score for match in matches},
        )
        keyword_chunks = await keyword_search_chunks(
            session,
            query=question,
            repository=repository,
            limit=retrieval_limit,
        )
        return merge_search_results(
            semantic_results=semantic_chunks,
            keyword_results=keyword_chunks,
            limit=limit,
        )


def _to_ask_source(chunk) -> AskSource:
    return AskSource(
        chunk_id=chunk.chunk_id,
        repository=chunk.repository,
        path=chunk.path,
        language=chunk.language,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        score=chunk.score,
    )


def _format_context(chunks: list) -> str:
    sections = []
    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Repository: {chunk.repository}",
                    f"File: {chunk.path}:{chunk.start_line}-{chunk.end_line}",
                    f"Language: {chunk.language or 'unknown'}",
                    "Content:",
                    chunk.content,
                ]
            )
        )
    return "\n\n---\n\n".join(sections)


def _stream_event(event_type: str, **payload) -> str:
    return json.dumps({"type": event_type, **payload}) + "\n"
