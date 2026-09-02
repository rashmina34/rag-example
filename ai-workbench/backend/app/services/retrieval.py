from app.models.document import DocumentSearchResult
from app.services.embeddings import generate_embedding
from app.services.vector_store import search_chunks


def retrieve(
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
) -> list[DocumentSearchResult]:

    # Validate query
    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    # Validate top_k
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    # 1. Convert the user's query into an embedding
    query_embedding = generate_embedding(query)

    # 2. Search ChromaDB using the query embedding
    matches = search_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
        document_id=document_id,
    )

    # 3. Convert database results into our Pydantic model
    return [
        DocumentSearchResult(
            id=match["id"],
            document_id=match["document_id"],
            filename=match["filename"],
            chunk_index=match["chunk_index"],
            text=match["text"],
            distance=match["distance"],
        )
        for match in matches
    ]