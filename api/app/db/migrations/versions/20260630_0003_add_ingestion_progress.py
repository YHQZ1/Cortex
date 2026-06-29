"""add ingestion progress

Revision ID: 20260630_0003
Revises: 20260629_0002
Create Date: 2026-06-30 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0003"
down_revision: str | Sequence[str] | None = "20260629_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ingestion_jobs", sa.Column("progress_stage", sa.String(length=64), nullable=True))
    op.add_column(
        "ingestion_jobs",
        sa.Column("progress_current", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("progress_total", sa.Integer(), server_default="1", nullable=False),
    )
    op.alter_column("ingestion_jobs", "progress_current", server_default=None)
    op.alter_column("ingestion_jobs", "progress_total", server_default=None)


def downgrade() -> None:
    op.drop_column("ingestion_jobs", "progress_total")
    op.drop_column("ingestion_jobs", "progress_current")
    op.drop_column("ingestion_jobs", "progress_stage")
