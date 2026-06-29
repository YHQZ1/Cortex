from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.pipeline.documents import DocumentChunk


class DocumentChunker:
    def __init__(self, *, chunk_size: int = 1200, chunk_overlap: int = 150) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\nclass ",
                "\n\ndef ",
                "\n\nfunction ",
                "\n\n",
                "\n",
                " ",
                "",
            ],
        )

    def split(self, content: str) -> list[DocumentChunk]:
        chunks = self._splitter.split_text(content)
        document_chunks: list[DocumentChunk] = []
        search_from = 0

        for ordinal, chunk in enumerate(chunks):
            start_index = content.find(chunk, max(0, search_from - 200))
            if start_index == -1:
                start_index = content.find(chunk)
            if start_index == -1:
                start_index = search_from

            end_index = start_index + len(chunk)
            start_line = content.count("\n", 0, start_index) + 1
            end_line = content.count("\n", 0, end_index) + 1
            search_from = end_index

            document_chunks.append(
                DocumentChunk(
                    ordinal=ordinal,
                    content=chunk,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        return document_chunks
