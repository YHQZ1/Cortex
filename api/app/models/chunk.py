from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Chunk(TimestampMixin, Base):
    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_file_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ingestion_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
