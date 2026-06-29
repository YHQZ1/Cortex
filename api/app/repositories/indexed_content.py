from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.repository import Repository
from app.models.source_file import SourceFile
from app.pipeline.chunking import DocumentChunker
from app.pipeline.filtering import infer_language, is_indexable_document
from app.pipeline.documents import SourceDocument
from app.utils.hashing import sha256_text


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: UUID
    repository_id: UUID
    repository: str
    path: str
    language: str | None
    start_line: int
    end_line: int
    content: str


async def ingest_documents(
    session: AsyncSession,
    *,
    ingestion_job_id: UUID,
    source_type: str,
    source_ref: str,
    repository_name: str,
    default_branch: str | None = None,
    documents: list[SourceDocument],
) -> dict:
    repository = await upsert_repository(
        session,
        source_type=source_type,
        source_ref=source_ref,
        name=repository_name,
        default_branch=default_branch,
    )
    chunker = DocumentChunker()

    indexed_files = 0
    indexed_chunks = 0
    skipped_files = 0
    indexed_paths: set[str] = set()
    chunk_records: list[tuple[Chunk, SourceFile]] = []

    for document in documents:
        if not is_indexable_document(document):
            skipped_files += 1
            continue

        indexed_paths.add(document.path)
        source_file = await upsert_source_file(session, repository_id=repository.id, document=document)
        await session.execute(delete(Chunk).where(Chunk.source_file_id == source_file.id))

        for document_chunk in chunker.split(document.content):
            chunk = Chunk(
                repository_id=repository.id,
                source_file_id=source_file.id,
                ingestion_job_id=ingestion_job_id,
                ordinal=document_chunk.ordinal,
                start_line=document_chunk.start_line,
                end_line=document_chunk.end_line,
                content=document_chunk.content,
                content_hash=sha256_text(document_chunk.content),
            )
            session.add(chunk)
            chunk_records.append((chunk, source_file))
            indexed_chunks += 1

        indexed_files += 1

    await session.flush()

    stale_files_query = delete(SourceFile).where(SourceFile.repository_id == repository.id)
    if indexed_paths:
        stale_files_query = stale_files_query.where(SourceFile.path.not_in(indexed_paths))
    await session.execute(stale_files_query)

    repository.last_indexed_at = datetime.now(UTC)
    await session.commit()

    chunks = [
        IndexedChunk(
            chunk_id=chunk.id,
            repository_id=repository.id,
            repository=source_ref,
            path=source_file.path,
            language=source_file.language,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            content=chunk.content,
        )
        for chunk, source_file in chunk_records
    ]

    return {
        "indexed_files": indexed_files,
        "indexed_chunks": indexed_chunks,
        "skipped_files": skipped_files,
        "repository_id": repository.id,
        "chunks": chunks,
    }


async def upsert_repository(
    session: AsyncSession,
    *,
    source_type: str,
    source_ref: str,
    name: str,
    default_branch: str | None,
) -> Repository:
    result = await session.execute(
        select(Repository).where(
            Repository.source_type == source_type,
            Repository.source_ref == source_ref,
        )
    )
    repository = result.scalar_one_or_none()

    if repository is None:
        repository = Repository(
            source_type=source_type,
            source_ref=source_ref,
            name=name,
            default_branch=default_branch,
        )
        session.add(repository)
        await session.flush()
    else:
        repository.name = name
        repository.default_branch = default_branch

    return repository


async def upsert_source_file(
    session: AsyncSession,
    *,
    repository_id: UUID,
    document: SourceDocument,
) -> SourceFile:
    result = await session.execute(
        select(SourceFile).where(
            SourceFile.repository_id == repository_id,
            SourceFile.path == document.path,
        )
    )
    source_file = result.scalar_one_or_none()
    content_hash = sha256_text(document.content)
    size_bytes = len(document.content.encode("utf-8"))

    if source_file is None:
        source_file = SourceFile(
            repository_id=repository_id,
            path=document.path,
            language=infer_language(document.path),
            content_hash=content_hash,
            size_bytes=size_bytes,
            last_indexed_at=datetime.now(UTC),
        )
        session.add(source_file)
        await session.flush()
    else:
        source_file.language = infer_language(document.path)
        source_file.content_hash = content_hash
        source_file.size_bytes = size_bytes
        source_file.last_indexed_at = datetime.now(UTC)

    return source_file
