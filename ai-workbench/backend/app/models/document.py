from pydantic import BaseModel
from pydantic import Field


class DocumentChunk(BaseModel):
    id: str

    document_id: str

    filename: str

    chunk_index: int

    text: str

    embedding: list[float] = Field(
        default_factory=list
    )


class DocumentIngestionResponse(BaseModel):
    document_id: str

    filename: str

    characters: int

    chunk_count: int

    chunks: list[DocumentChunk]


class DocumentSearchRequest(BaseModel):
    query: str

    top_k: int = 5


class DocumentSearchResult(BaseModel):
    id: str

    document_id: str

    filename: str

    chunk_index: int

    text: str

    distance: float