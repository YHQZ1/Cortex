from collections.abc import Iterable

import httpx

from app.config import Settings


class OllamaEmbeddingProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        payload = {
            "model": self._settings.embedding_model,
            "input": list(texts),
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self._settings.ollama_url}/api/embed", json=payload)
            response.raise_for_status()

        data = response.json()
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Ollama embedding response did not include embeddings.")
        return embeddings
