from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.providers.embeddings import OllamaEmbeddingProvider
from app.providers.llm import OllamaLLMProvider
from app.providers.vector_store import QdrantVectorStore
from app.repositories.search import get_semantic_search_results
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
        query_vector = await self._embeddings.embed_text(question)
        matches = await self._vector_store.search(
            vector=query_vector,
            repository=repository,
            limit=limit,
        )
        chunks = await get_semantic_search_results(
            session,
            scores_by_chunk_id={match.chunk_id: match.score for match in matches},
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
                AskSource(
                    chunk_id=chunk.chunk_id,
                    repository=chunk.repository,
                    path=chunk.path,
                    language=chunk.language,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=chunk.score,
                )
                for chunk in chunks
            ],
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
