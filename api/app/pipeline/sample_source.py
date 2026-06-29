from app.pipeline.documents import SourceDocument


def get_sample_documents() -> list[SourceDocument]:
    return [
        SourceDocument(
            path="README.md",
            content="""# Cortex

Cortex indexes source repositories and turns them into searchable context.

The ingestion flow fetches files, filters noisy paths, chunks useful content,
and eventually embeds those chunks into a vector database.
""",
        ),
        SourceDocument(
            path="api/app/example.py",
            content='''from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def chunk_repository_file(path: str, content: str) -> list[str]:
    """Split a repository file into retrievable chunks."""
    if not content.strip():
        return []
    return [content]
''',
        ),
        SourceDocument(
            path="node_modules/ignored.js",
            content="console.log('this should not be indexed')",
        ),
    ]
