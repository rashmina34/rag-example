import json

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field

from app.services.conversation import (
    ChatMessage,
    trim_messages,
)

from app.services.llm import generate_response
from app.services.llm import stream_chat


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."


class ChatRequest(BaseModel):
    message: str


class ChatStreamRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)

    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


@router.post("")
def chat(
    request: ChatRequest,
):

    try:

        response = generate_response(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
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


def sse(event: dict) -> str:
    """Format one Server-Sent Event."""

    return f"data: {json.dumps(event)}\n\n"


@router.post("/stream")
def chat_stream(
    request: ChatStreamRequest,
):
    """Multi-turn chat. The client sends the whole conversation each time
    and receives the answer as a stream of Server-Sent Events:

        data: {"text": "..."}              (many times)
        data: {"done": true, "dropped": 0} (once, at the end)
        data: {"error": "..."}             (instead, if something fails)
    """

    if request.messages[-1].role != "user":

        raise HTTPException(
            status_code=400,
            detail="The last message must be from the user.",
        )

    if not request.messages[-1].content.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    messages, dropped = trim_messages(
        request.messages
    )

    def event_stream():

        try:

            for text in stream_chat(
                messages=messages,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
            ):

                yield sse({"text": text})

            yield sse({"done": True, "dropped": dropped})

        except Exception as error:

            yield sse({"error": str(error)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
