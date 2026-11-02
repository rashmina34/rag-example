import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from google.genai.errors import ServerError

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Check your backend/.env file."
    )

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=30_000,
    ),
)

# Streaming keeps one connection open while the answer is written, so it
# needs a longer timeout than a normal request.
stream_client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=120_000,
    ),
)

MODEL = (
    os.getenv("GEMINI_PRIMARY_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-3.5-flash"
)


# Free-tier keys allow only a few requests per minute, so a burst of
# calls (for example an evaluation run) can hit a 429. The error says how
# long to wait, so wait that long and try again.
MAX_RATE_LIMIT_WAIT = 65


def rate_limit_delay(error: ClientError) -> float | None:
    """Seconds to wait if ``error`` is a rate limit (429), else None."""

    if error.code != 429:
        return None

    match = re.search(
        r"retry in ([\d.]+)s",
        str(error),
    )

    delay = float(match.group(1)) + 1 if match else 30

    return min(delay, MAX_RATE_LIMIT_WAIT)


def with_retries(call):
    """Run ``call()``, retrying server errors and rate limits."""

    for attempt in range(4):

        try:
            return call()

        except ServerError:
            if attempt >= 2:
                raise

            time.sleep(2 ** attempt)

        except ClientError as error:
            delay = rate_limit_delay(error)

            if delay is None or attempt >= 3:
                raise

            time.sleep(delay)

    raise RuntimeError("Unable to generate response.")


def generate_response(
    user_prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.7,
) -> str:

    def call():
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
            ),
        )

        return response.text

    return with_retries(call)


def stream_chat(
    messages: list,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.7,
):
    """Yield the model's answer piece by piece.

    ``messages`` is the whole conversation so far (objects with ``role``
    "user" or "assistant" and ``content``), ending with the user's turn.
    """

    contents = [
        types.Content(
            role="user" if message.role == "user" else "model",
            parts=[types.Part(text=message.content)],
        )
        for message in messages
    ]

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
    )

    for attempt in range(3):

        started = False

        try:

            for chunk in stream_client.models.generate_content_stream(
                model=MODEL,
                contents=contents,
                config=config,
            ):

                if chunk.text:
                    started = True
                    yield chunk.text

            return

        except ServerError:

            # Retrying after text was already sent would repeat it.
            if started or attempt == 2:
                raise

            time.sleep(2 ** attempt)


def generate_json(
    user_prompt: str,
    schema,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.0,
):
    """Ask the model for JSON that matches a Pydantic ``schema``.

    Returns an instance of ``schema``.
    """

    def call():
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

        return schema.model_validate_json(response.text)

    return with_retries(call)
