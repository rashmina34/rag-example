const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function uploadDocument(file, chunkSize, chunkOverlap) {
    const formData = new FormData();
    formData.append("file", file);

    const params = new URLSearchParams();

    if (chunkSize) params.set("chunk_size", chunkSize);
    if (chunkOverlap !== undefined) params.set("chunk_overlap", chunkOverlap);

    const query = params.toString() ? `?${params}` : "";

    const response = await fetch(
        `${API_BASE_URL}/documents/upload${query}`,
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
    documentId = null,
    includePrompt = false
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
                include_prompt: includePrompt,
            }),
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to ask question");
    }

    return response.json();
}

async function postJson(path, body, fallbackMessage) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || fallbackMessage);
    }

    return response.json();
}


export function chunkText(text, chunkSize, chunkOverlap) {
    return postJson(
        "/lab/chunk",
        {
            text,
            chunk_size: chunkSize,
            chunk_overlap: chunkOverlap,
        },
        "Failed to chunk text"
    );
}


export function compareTexts(texts) {
    return postJson(
        "/lab/similarity",
        { texts },
        "Failed to compare texts"
    );
}


// Multi-turn chat. The whole conversation is sent each time, and the
// answer arrives as Server-Sent Events: {text}, then {done}, or {error}.
export async function streamChat({
    messages,
    systemPrompt,
    temperature,
    signal,
    onText,
}) {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            messages,
            system_prompt: systemPrompt,
            temperature,
        }),
        signal,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to start chat");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let dropped = 0;

    while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // events are separated by a blank line
        const events = buffer.split("\n\n");
        buffer = events.pop();

        for (const raw of events) {
            if (!raw.startsWith("data: ")) continue;

            const event = JSON.parse(raw.slice(6));

            if (event.error) throw new Error(event.error);
            if (event.text) onText(event.text);
            if (event.done) dropped = event.dropped || 0;
        }
    }

    return { dropped };
}



export function runEvaluation(request) {
    return postJson(
        "/evaluations/run",
        request,
        "Failed to run evaluation"
    );
}


export async function listEvaluationRuns() {
    const response = await fetch(`${API_BASE_URL}/evaluations/runs`);

    if (!response.ok) throw new Error("Failed to load past runs");

    return response.json();
}


export async function deleteEvaluationRun(id) {
    const response = await fetch(
        `${API_BASE_URL}/evaluations/runs/${id}`,
        { method: "DELETE" }
    );

    if (!response.ok) throw new Error("Failed to delete run");
}
