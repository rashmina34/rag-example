from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]

    content: str


# A model has a limited context window, so a long chat cannot be sent
# in full forever. This is a simple character budget (roughly 4 chars
# per token), good enough to teach the idea of context trimming.
MAX_HISTORY_CHARS = 12_000


def trim_messages(
    messages: list[ChatMessage],
    max_chars: int = MAX_HISTORY_CHARS,
) -> tuple[list[ChatMessage], int]:
    """Drop the oldest messages until the history fits the budget.

    Always keeps the latest message, and makes sure the history starts
    with a user message. Returns (kept_messages, dropped_count).
    """

    kept: list[ChatMessage] = []

    total = 0

    for message in reversed(messages):

        total += len(message.content)

        if kept and total > max_chars:
            break

        kept.append(message)

    kept.reverse()

    while kept and kept[0].role != "user":
        kept.pop(0)

    return kept, len(messages) - len(kept)
