from pathlib import Path


def load_text_file(
    file_path: str,
) -> str:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if path.suffix.lower() != ".txt":
        raise ValueError(
            "Only .txt files are supported currently."
        )

    return path.read_text(
        encoding="utf-8"
    )