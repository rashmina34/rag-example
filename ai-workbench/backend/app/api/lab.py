from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field

from app.services.chunking import (
    chunk_text_with_spans,
)

from app.services.embeddings import (
    generate_embedding,
)

from app.services.similarity import (
    cosine_similarity_matrix,
    project_to_2d,
)


router = APIRouter(
    prefix="/lab",
    tags=["lab"],
)


MAX_TEXTS = 12


class ChunkRequest(BaseModel):
    text: str

    chunk_size: int = Field(default=500, ge=1, le=5000)

    chunk_overlap: int = Field(default=50, ge=0, le=4999)


class SimilarityRequest(BaseModel):
    texts: list[str]


@router.post("/chunk")
def chunk(
    request: ChunkRequest,
):
    """Split text into chunks without calling any AI model."""

    try:

        cleaned, chunks = chunk_text_with_spans(
            text=request.text,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "cleaned_text": cleaned,
        "characters": len(cleaned),
        "chunk_size": request.chunk_size,
        "chunk_overlap": request.chunk_overlap,
        "chunk_count": len(chunks),
        "chunks": [
            {
                "index": index,
                "length": len(item["text"]),
                **item,
            }
            for index, item in enumerate(chunks)
        ],
    }


@router.post("/similarity")
def similarity(
    request: SimilarityRequest,
):
    """Embed a few texts, then compare and plot them."""

    texts = [
        text.strip()
        for text in request.texts
        if text.strip()
    ]

    if len(texts) < 2:

        raise HTTPException(
            status_code=400,
            detail="Enter at least 2 texts.",
        )

    if len(texts) > MAX_TEXTS:

        raise HTTPException(
            status_code=400,
            detail=f"Enter at most {MAX_TEXTS} texts.",
        )

    try:

        vectors = [
            generate_embedding(text)
            for text in texts
        ]

        matrix = cosine_similarity_matrix(vectors)

        points = project_to_2d(vectors)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return {
        "dimensions": len(vectors[0]),
        "texts": texts,
        "similarity": matrix,
        "points": [
            {"x": x, "y": y}
            for x, y in points
        ],
    }
