const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
        `${API_BASE_URL}/documents/upload`,
        {
            method: "POST",
            body: formData,
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upload document");
    }

    return response.json();
}


export async function askQuestion(
    question,
    topK = 5,
    documentId = null
) {
    const response = await fetch(
        `${API_BASE_URL}/documents/ask`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question,
                top_k: topK,
                document_id: documentId,
            }),
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to ask question");
    }

    return response.json();
}