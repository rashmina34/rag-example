import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
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

MODEL = (
    os.getenv("GEMINI_PRIMARY_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-3.5-flash"
)


def generate_response(
    user_prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.7,
) -> str:

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            )

            return response.text

        except ServerError:
            if attempt == 2:
                raise

            time.sleep(2 ** attempt)

    raise RuntimeError("Unable to generate response.")