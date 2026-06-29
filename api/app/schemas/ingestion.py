from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.ingestion_job import IngestionJobStatus, IngestionSourceType


class IngestionJobCreate(BaseModel):
    source_type: IngestionSourceType = IngestionSourceType.GITHUB
    source_ref: str | None = Field(
        default=None,
        description="Source target, such as a GitHub owner/repo. Optional while the pipeline is stubbed.",
        max_length=512,
    )


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: IngestionJobStatus
    source_type: IngestionSourceType
    source_ref: str | None
    message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
