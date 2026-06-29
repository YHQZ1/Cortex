from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Repository(TimestampMixin, Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("source_type", "source_ref", name="uq_repositories_source_type_source_ref"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
