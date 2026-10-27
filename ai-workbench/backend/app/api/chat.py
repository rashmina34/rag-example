from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.llm import generate_response


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(
    request: ChatRequest,
):

    try:

        response = generate_response(
            system_prompt=(
                "You are a helpful AI assistant."
            ),
            user_prompt=request.message,
            temperature=0.7,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return {
        "response": response
    }