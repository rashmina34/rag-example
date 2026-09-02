from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from app.models.document import (
    DocumentIngestionResponse,
)

from app.services.document_ingestion import (
    ingest_document,
)
from app.models.document import (
    DocumentSearchRequest,
)

from app.services.embeddings import (
    generate_embedding,
)

from app.services.vector_store import (
    search_chunks,
)

from app.models.document import (
    RAGRequest,
)

from app.services.rag import (
    answer_question,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "/upload",
    response_model=DocumentIngestionResponse,
)
async def upload_document(
    file: UploadFile = File(...),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(
        ".txt"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported.",
        )

    try:

        content = await file.read()

        chunks = ingest_document(
            filename=file.filename,
            content=content,
            chunk_size=500,
            chunk_overlap=50,
        )

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail="No chunks were generated.",
            )

        document_id = chunks[0].document_id

        text_length = sum(
            len(chunk.text)
            for chunk in chunks
        )

        return DocumentIngestionResponse(
            document_id=document_id,
            filename=file.filename,
            characters=text_length,
            chunk_count=len(chunks),
            chunks=chunks,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
        
@router.post("/search")
def search_documents(
    request: DocumentSearchRequest,
):

    if not request.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    try:

        query_embedding = generate_embedding(
            request.query
        )

        results = search_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "results": results,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
        
@router.post("/ask")
def ask_documents(
    request: RAGRequest,
):

    try:

        return answer_question(
            question=request.question,
            top_k=request.top_k,
            document_id=request.document_id,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )