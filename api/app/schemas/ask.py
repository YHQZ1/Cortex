from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    repository: str | None = Field(default=None, max_length=512)
    limit: int = Field(default=5, ge=1, le=12)
    mode: str = Field(default="repository", pattern="^(repository|general)$")

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        return question


class AskSource(BaseModel):
    chunk_id: UUID
    repository: str
    path: str
    language: str | None
    start_line: int
    end_line: int
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[AskSource]
