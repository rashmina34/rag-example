import numpy as np


def cosine_similarity_matrix(
    vectors: list[list[float]],
) -> list[list[float]]:

    matrix = np.array(vectors, dtype=float)

    norms = np.linalg.norm(
        matrix,
        axis=1,
        keepdims=True,
    )

    norms[norms == 0] = 1.0

    normalized = matrix / norms

    return (normalized @ normalized.T).tolist()


def project_to_2d(
    vectors: list[list[float]],
) -> list[list[float]]:
    """Reduce embeddings to 2 dimensions with PCA (via SVD)."""

    matrix = np.array(vectors, dtype=float)

    centered = matrix - matrix.mean(axis=0)

    _, _, components = np.linalg.svd(
        centered,
        full_matrices=False,
    )

    projected = centered @ components[:2].T

    # With fewer than 2 principal components (e.g. 2 texts)
    # pad the missing axis with zeros so the shape stays (n, 2).
    if projected.shape[1] < 2:
        projected = np.pad(
            projected,
            ((0, 0), (0, 2 - projected.shape[1])),
        )

    return projected.tolist()
