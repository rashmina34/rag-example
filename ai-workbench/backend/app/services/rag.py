from app.services.llm import generate_response
from app.services.retrieval import retrieve


RAG_SYSTEM_PROMPT = """
You are a helpful AI assistant.

Answer the user's question using the provided
context.

Rules:
1. Use the context as the primary source of information.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information,
   clearly say that the information is not available
   in the provided documents.
4. Give a concise and clear answer.
"""


def build_context(results) -> str:

    if not results:
        return ""

    context_parts = []

    for index, result in enumerate(results):

        context_parts.append(
            f"""
--- Source {index + 1} ---
File: {result.filename}
Chunk: {result.chunk_index}

{result.text}
"""
        )

    return "\n".join(context_parts)


def build_rag_prompt(
    question: str,
    context: str,
) -> str:

    return f"""
{RAG_SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""


def answer_question(
    question: str,
    top_k: int = 5,
    document_id: str | None = None,
):

    results = retrieve(
        query=question,
        top_k=top_k,
        document_id=document_id,
    )

    context = build_context(
        results
    )

    if not context:

        return {
            "question": question,
            "answer": (
                "I could not find relevant "
                "information in the documents."
            ),
            "sources": [],
        }

    prompt = build_rag_prompt(
        question=question,
        context=context,
    )

    answer = generate_response(
        prompt
    )

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "filename": result.filename,
                "chunk_index": result.chunk_index,
                "distance": result.distance,
                "text": result.text,
            }
            for result in results
        ],
    }