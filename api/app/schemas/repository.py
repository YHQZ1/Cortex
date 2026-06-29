from datetime import datetime

from pydantic import BaseModel


class RepositorySummary(BaseModel):
    source_type: str
    source_ref: str
    name: str
    default_branch: str | None
    last_indexed_at: datetime | None
    file_count: int
    chunk_count: int
