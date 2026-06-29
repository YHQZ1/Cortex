from uuid import UUID

from pydantic import BaseModel


class ChunkPreview(BaseModel):
    chunk_id: UUID
    repository: str
    path: str
    language: str | None
    start_line: int
    end_line: int
    content: str
