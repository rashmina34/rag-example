import chromadb

from app.models.document import (
    DocumentChunk,
)


CHROMA_PATH = "./chroma_db"


client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


collection = client.get_or_create_collection(
    name="ai_workbench_documents",
    metadata={
        "hnsw:space": "cosine"
    },
)


def add_chunks(
    chunks: list[DocumentChunk],
):
    if not chunks:
        return

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in chunks:

        ids.append(chunk.id)

        embeddings.append(
            chunk.embedding
        )

        documents.append(
            chunk.text
        )

        metadatas.append(
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
            }
        )

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def get_collection_count() -> int:

    return collection.count()


def delete_document(
    document_id: str,
):

    collection.delete(
        where={
            "document_id": document_id
        }
    )
    
def search_chunks(
    query_embedding: list[float],
    top_k: int = 5,
    document_id: str | None =  None
):

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=top_k,
    )

    matches = []

    ids = results.get(
        "ids",
        [[]]
    )[0]

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    for index in range(
        len(ids)
    ):

        metadata = metadatas[index]

        matches.append(
            {
                "id": ids[index],
                "document_id": metadata[
                    "document_id"
                ],
                "filename": metadata[
                    "filename"
                ],
                "chunk_index": metadata[
                    "chunk_index"
                ],
                "text": documents[index],
                "distance": distances[index],
            }
        )

    return matches