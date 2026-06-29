from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    repository: str | None = Field(
        default=None,
        description="Optional source_ref filter, such as YHQZ1/ESX.",
        max_length=512,
    )
    limit: int = Field(default=10, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Search query cannot be empty.")
        return query


class SearchResult(BaseModel):
    chunk_id: UUID
    repository: str
    path: str
    language: str | None
    start_line: int
    end_line: int
    content: str


class SemanticSearchResult(SearchResult):
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
