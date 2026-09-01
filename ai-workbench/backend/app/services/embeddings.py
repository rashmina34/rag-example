import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


client = genai.Client(
    api_key=API_KEY
)


EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
)


def generate_embedding(
    text: str,
) -> list[float]:

    if not text.strip():
        raise ValueError(
            "Text cannot be empty."
        )

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no embedding."
        )

    return response.embeddings[0].values