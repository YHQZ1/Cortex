import json
import re
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

SUBJECT_STOPWORDS = {
    "about",
    "code",
    "codebase",
    "does",
    "explain",
    "handle",
    "handles",
    "how",
    "project",
    "repo",
    "repository",
    "tell",
    "the",
    "this",
    "what",
    "where",
    "which",
}

RELEVANCE_ALIASES = {
    "queue": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task"},
    "queuing": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task"},
    "queueing": {"queue", "queued", "queuing", "queueing", "celery", "redis", "broker", "worker", "task"},
}


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
        mode: str = "repository",
    ) -> AskResponse:
        if mode == "general":
            answer = await self._llm.generate_general_answer(question=question)
            return AskResponse(question=question, answer=answer, sources=[])

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

        if not _is_context_relevant(question, chunks):
            return AskResponse(
                question=question,
                answer=_irrelevant_context_answer(question, repository),
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
        mode: str = "repository",
    ) -> AsyncIterator[str]:
        if mode == "general":
            yield _stream_event("sources", sources=[])
            async for token in self._llm.stream_general_answer(question=question):
                yield _stream_event("token", content=token)
            yield _stream_event("done")
            return

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

        if not _is_context_relevant(question, chunks):
            yield _stream_event("sources", sources=[])
            yield _stream_event("token", content=_irrelevant_context_answer(question, repository))
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


def _is_context_relevant(question: str, chunks: list) -> bool:
    subject_terms = _extract_subject_terms(question)
    if not subject_terms:
        return True

    context = " ".join(f"{chunk.path} {chunk.content}" for chunk in chunks).lower()
    return any(term in context for term in subject_terms)


def _extract_subject_terms(question: str) -> set[str]:
    raw_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z0-9_.-]+", question)
        if len(term) >= 3 and term.lower() not in SUBJECT_STOPWORDS
    }
    expanded = set(raw_terms)
    for term in raw_terms:
        expanded.update(RELEVANCE_ALIASES.get(term, set()))
    return expanded


def _irrelevant_context_answer(question: str, repository: str | None) -> str:
    scope = f" in {repository}" if repository else " in the indexed repositories"
    return (
        f"I could not find relevant indexed context for this question{scope}. "
        "Cortex answers from repository context, so ask about something present in the indexed codebase "
        "or ingest a repository that contains this topic."
    )


def _stream_event(event_type: str, **payload) -> str:
    return json.dumps({"type": event_type, **payload}) + "\n"
