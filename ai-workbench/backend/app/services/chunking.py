def clean_text(text: str) -> str:

    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    lines = [
        line
        for line in lines
        if line
    ]

    return "\n".join(lines)


def chunk_text_with_spans(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[str, list[dict]]:
    """Chunk text and report where each chunk sits in the cleaned text.

    Returns (cleaned_text, chunks) where every chunk is a dict with
    ``text``, ``start`` and ``end`` (character offsets into cleaned_text).
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0."
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    if not text.strip():
        return "", []

    text = clean_text(text)

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                {
                    "text": chunk,
                    "start": start,
                    "end": end,
                }
            )

        if end >= text_length:
            break

        start = end - chunk_overlap

    return text, chunks


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:

    _, chunks = chunk_text_with_spans(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return [chunk["text"] for chunk in chunks]
