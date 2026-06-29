from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    path: str
    content: str


@dataclass(frozen=True)
class DocumentChunk:
    ordinal: int
    content: str
    start_line: int
    end_line: int
