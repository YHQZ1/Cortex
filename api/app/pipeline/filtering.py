from pathlib import PurePosixPath

from app.pipeline.documents import SourceDocument

MAX_TEXT_FILE_BYTES = 512_000

SKIPPED_PATH_PARTS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

SKIPPED_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "yarn.lock",
}

SKIPPED_SUFFIXES = {
    ".gen.go",
    ".pb.go",
    "_grpc.pb.go",
}

ALLOWED_EXTENSIONS = {
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

LANGUAGE_BY_EXTENSION = {
    ".css": "css",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".md": "markdown",
    ".py": "python",
    ".rs": "rust",
    ".sql": "sql",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def get_path_skip_reason(path_value: str) -> str | None:
    path = PurePosixPath(path_value)

    if any(part in SKIPPED_PATH_PARTS for part in path.parts):
        return "ignored path"

    if path.name in SKIPPED_FILENAMES:
        return "lockfile"

    if any(path.name.endswith(suffix) for suffix in SKIPPED_SUFFIXES):
        return "generated file"

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return "unsupported extension"

    return None


def get_document_skip_reason(document: SourceDocument) -> str | None:
    path_reason = get_path_skip_reason(document.path)
    if path_reason is not None:
        return path_reason

    if len(document.content.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
        return "too large"

    if "\x00" in document.content:
        return "binary content"

    if not document.content.strip():
        return "empty file"

    return None


def is_indexable_document(document: SourceDocument) -> bool:
    return get_document_skip_reason(document) is None


def infer_language(path: str) -> str | None:
    return LANGUAGE_BY_EXTENSION.get(PurePosixPath(path).suffix.lower())
