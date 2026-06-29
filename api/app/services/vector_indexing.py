from collections.abc import Awaitable, Callable, Sequence

from app.config import Settings
from app.providers.embeddings import OllamaEmbeddingProvider
from app.providers.vector_store import QdrantVectorStore
from app.repositories.indexed_content import IndexedChunk


class VectorIndexingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embeddings = OllamaEmbeddingProvider(settings)
        self._vector_store = QdrantVectorStore(settings)

    async def index_chunks(
        self,
        chunks: Sequence[IndexedChunk],
        progress_callback: Callable[[str, int, int], Awaitable[None]] | None = None,
    ) -> int:
        if not chunks:
            return 0

        points = []
        processed_chunks = 0
        for batch in _batched(chunks, size=32):
            vectors = await self._embeddings.embed_texts(chunk.content for chunk in batch)
            for chunk, vector in zip(batch, vectors, strict=True):
                if len(vector) != self._settings.embedding_dimension:
                    raise ValueError(
                        "Embedding dimension mismatch: "
                        f"expected {self._settings.embedding_dimension}, got {len(vector)}."
                    )
                points.append(
                    {
                        "chunk_id": str(chunk.chunk_id),
                        "vector": vector,
                        "path": chunk.path,
                        "language": chunk.language,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    }
                )
            processed_chunks += len(batch)
            if progress_callback is not None:
                await progress_callback("embedding chunks", processed_chunks, len(chunks))

        first_chunk = chunks[0]
        if progress_callback is not None:
            await progress_callback("writing vectors", 0, len(points))
        await self._vector_store.upsert_chunks(
            repository_id=first_chunk.repository_id,
            repository=first_chunk.repository,
            points=points,
        )
        if progress_callback is not None:
            await progress_callback("writing vectors", len(points), len(points))
        return len(points)


def _batched[T](items: Sequence[T], *, size: int) -> list[Sequence[T]]:
    return [items[index : index + size] for index in range(0, len(items), size)]
