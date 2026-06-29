from dataclasses import dataclass
from uuid import UUID

import httpx

from app.config import Settings


@dataclass(frozen=True)
class VectorSearchMatch:
    chunk_id: UUID
    score: float


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._collection_url = f"{settings.qdrant_url}/collections/{settings.qdrant_collection}"

    async def ensure_collection(self) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._collection_url)
            if response.status_code == 200:
                return
            if response.status_code != 404:
                response.raise_for_status()

            create_response = await client.put(
                self._collection_url,
                json={
                    "vectors": {
                        "size": self._settings.embedding_dimension,
                        "distance": "Cosine",
                    }
                },
            )
            create_response.raise_for_status()

    async def upsert_chunks(
        self,
        *,
        repository_id: UUID,
        repository: str,
        points: list[dict],
    ) -> None:
        await self.ensure_collection()
        async with httpx.AsyncClient(timeout=30.0) as client:
            delete_response = await client.post(
                f"{self._collection_url}/points/delete",
                json={
                    "filter": {
                        "must": [
                            {
                                "key": "repository_id",
                                "match": {"value": str(repository_id)},
                            }
                        ]
                    }
                },
            )
            delete_response.raise_for_status()

            if not points:
                return

            upsert_response = await client.put(
                f"{self._collection_url}/points",
                json={
                    "points": [
                        {
                            "id": point["chunk_id"],
                            "vector": point["vector"],
                            "payload": {
                                "chunk_id": point["chunk_id"],
                                "repository_id": str(repository_id),
                                "repository": repository,
                                "path": point["path"],
                                "language": point["language"],
                                "start_line": point["start_line"],
                                "end_line": point["end_line"],
                            },
                        }
                        for point in points
                    ]
                },
            )
            upsert_response.raise_for_status()

    async def search(
        self,
        *,
        vector: list[float],
        limit: int,
        repository: str | None = None,
    ) -> list[VectorSearchMatch]:
        await self.ensure_collection()
        filters = []
        if repository is not None:
            filters.append({"key": "repository", "match": {"value": repository}})

        payload: dict = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
        }
        if filters:
            payload["filter"] = {"must": filters}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self._collection_url}/points/search", json=payload)
            response.raise_for_status()

        results = response.json().get("result", [])
        return [
            VectorSearchMatch(
                chunk_id=UUID(item["payload"]["chunk_id"]),
                score=item["score"],
            )
            for item in results
            if item.get("payload", {}).get("chunk_id") is not None
        ]
