from fastapi import APIRouter
from pydantic import BaseModel

from app.services.embeddings import (
    generate_embedding,
)


router = APIRouter(
    prefix="/embeddings",
    tags=["embeddings"],
)


class EmbeddingRequest(BaseModel):
    text: str


@router.post("")
def create_embedding(
    request: EmbeddingRequest,
):

    vector = generate_embedding(
        request.text
    )

    return {
        "text": request.text,
        "dimensions": len(vector),
        "embedding": vector,
    }