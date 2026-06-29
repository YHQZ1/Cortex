"""create repository file chunk tables

Revision ID: 20260629_0002
Revises: 20260629_0001
Create Date: 2026-06-29 00:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0002"
down_revision: str | Sequence[str] | None = "20260629_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repositories")),
        sa.UniqueConstraint(
            "source_type",
            "source_ref",
            name="uq_repositories_source_type_source_ref",
        ),
    )
    op.create_index(op.f("ix_repositories_source_type"), "repositories", ["source_type"], unique=False)

    op.create_table(
        "source_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name=op.f("fk_source_files_repository_id_repositories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_files")),
        sa.UniqueConstraint("repository_id", "path", name="uq_source_files_repository_id_path"),
    )
    op.create_index(op.f("ix_source_files_repository_id"), "source_files", ["repository_id"], unique=False)

    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=False),
        sa.Column("ingestion_job_id", sa.Uuid(), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_job_id"],
            ["ingestion_jobs.id"],
            name=op.f("fk_chunks_ingestion_job_id_ingestion_jobs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name=op.f("fk_chunks_repository_id_repositories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            ["source_files.id"],
            name=op.f("fk_chunks_source_file_id_source_files"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunks")),
    )
    op.create_index(op.f("ix_chunks_ingestion_job_id"), "chunks", ["ingestion_job_id"], unique=False)
    op.create_index(op.f("ix_chunks_repository_id"), "chunks", ["repository_id"], unique=False)
    op.create_index(op.f("ix_chunks_source_file_id"), "chunks", ["source_file_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chunks_source_file_id"), table_name="chunks")
    op.drop_index(op.f("ix_chunks_repository_id"), table_name="chunks")
    op.drop_index(op.f("ix_chunks_ingestion_job_id"), table_name="chunks")
    op.drop_table("chunks")
    op.drop_index(op.f("ix_source_files_repository_id"), table_name="source_files")
    op.drop_table("source_files")
    op.drop_index(op.f("ix_repositories_source_type"), table_name="repositories")
    op.drop_table("repositories")
