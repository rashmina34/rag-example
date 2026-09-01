from uuid import uuid4

from app.models.document import (
    DocumentChunk,
)

from app.services.chunking import (
    chunk_text,
    clean_text,
)

from app.services.embeddings import (
    generate_embedding,
)

from app.services.vector_store import (
    add_chunks,
)


def ingest_document(
    filename: str,
    content: bytes,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[DocumentChunk]:

    try:

        text = content.decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        raise ValueError(
            "File must be UTF-8 encoded."
        )

    text = clean_text(text)

    if not text:

        raise ValueError(
            "Document is empty."
        )

    chunks = chunk_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    document_id = str(uuid4())

    document_chunks = []

    for index, chunk in enumerate(
        chunks
    ):

        embedding = generate_embedding(
            chunk
        )

        document_chunk = DocumentChunk(
            id=str(uuid4()),
            document_id=document_id,
            filename=filename,
            chunk_index=index,
            text=chunk,
            embedding=embedding,
        )

        document_chunks.append(
            document_chunk
        )

    add_chunks(
        document_chunks
    )

    return document_chunks