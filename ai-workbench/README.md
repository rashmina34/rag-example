# AI Workbench

A learning project for building AI applications on top of Google Gemini. It has a FastAPI backend and a Next.js frontend, and covers four things:

- **Chat**: single-turn chat with Gemini.
- **Embeddings**: turn text into vectors with `gemini-embedding-001`.
- **RAG**: upload `.txt` documents, chunk and embed them into ChromaDB, then ask questions grounded in those documents.
- **Workflows**: multi-step pipelines of `llm` and `rag` steps. Steps are stored in SQLite, can use each other's output as prompt variables, and every execution is recorded.

```
ai-workbench/
├── backend/
│   ├── main.py                  # entry point: `python3 main.py`
│   ├── requirements.txt
│   ├── .env.example
│   ├── ai_workbench.db          # SQLite (workflows + execution history), created on first run
│   ├── chroma_db/               # ChromaDB vector store, created on first run
│   └── app/
│       ├── main.py              # FastAPI app, CORS, router registration
│       ├── api/                 # HTTP routes: chat, documents, embeddings, workflows
│       ├── models/              # Pydantic schemas + SQLAlchemy tables
│       └── services/            # llm, embeddings, chunking, vector_store, retrieval, rag, workflow execution
├── frontend/                    # Next.js 16 / React 19 / Tailwind 4 UI
└── docs/test.txt                # sample document for trying out RAG
```

## Requirements

- Python 3.11 or newer (developed on 3.13)
- Node.js 20 or newer (frontend only)
- A [Gemini API key](https://aistudio.google.com/apikey)

## Run the backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then put your real key in GEMINI_API_KEY

python3 main.py
```

The API listens on <http://127.0.0.1:8000>. Interactive docs are at <http://127.0.0.1:8000/docs>.

Run it from inside `backend/`. `main.py` starts uvicorn with `app.main:app` and auto-reload. The SQLite and Chroma files are always created in `backend/`, whatever directory you start from.

### Configuration

`backend/.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | none (required) | Gemini API key. The app refuses to start without it. |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Model for chat, RAG answers and workflow `llm` steps. `GEMINI_PRIMARY_MODEL` takes precedence if set. |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model. |

Optional environment variables for `main.py`: `HOST` (default `127.0.0.1`), `PORT` (default `8000`), `RELOAD` (default `true`).

Google retires models regularly. If you get a `404 NOT_FOUND ... no longer available` error, change `GEMINI_MODEL` to a current model.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The frontend calls the backend at `http://127.0.0.1:8000/api` (see `frontend/app/api.js`), and the backend allows CORS from ports 3000 and 5173.

## API

All routes are under `/api`, except `/` and `/health`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| POST | `/api/chat` | `{"message": "..."}` returns `{"response": "..."}` |
| POST | `/api/embeddings` | `{"text": "..."}` returns the embedding vector and its dimensions |
| POST | `/api/documents/upload` | Multipart `file` (`.txt`, UTF-8). Chunks it (500 chars, 50 overlap), embeds each chunk and stores them in ChromaDB. |
| POST | `/api/documents/search` | `{"query": "...", "top_k": 5}` returns the nearest chunks |
| POST | `/api/documents/ask` | `{"question": "...", "top_k": 5, "document_id": null}` returns a RAG answer with its sources. Set `document_id` to restrict retrieval to one document. |
| POST | `/api/workflows` | Create a workflow |
| GET | `/api/workflows` | List workflows |
| GET | `/api/workflows/{id}` | Get a workflow with its steps |
| DELETE | `/api/workflows/{id}` | Delete a workflow |
| POST | `/api/workflows/{id}/execute` | `{"input": "..."}` runs the workflow |
| GET | `/api/workflows/{id}/executions` | Execution history |
| GET | `/api/workflows/{id}/executions/{execution_id}` | One execution with per-step results |

### Try it

```bash
# chat
curl -X POST localhost:8000/api/chat -H 'content-type: application/json' \
  -d '{"message": "Explain embeddings in one sentence"}'

# upload a document, then ask about it
curl -F file=@../docs/test.txt localhost:8000/api/documents/upload
curl -X POST localhost:8000/api/documents/ask -H 'content-type: application/json' \
  -d '{"question": "What are large language models?"}'
```

## How RAG works

1. **Ingest** (`document_ingestion.py`): decode the UTF-8 text, clean it (strip blank lines), and split it into overlapping chunks (`chunking.py`).
2. **Embed** (`embeddings.py`): each chunk goes through Gemini `embed_content`.
3. **Store** (`vector_store.py`): chunks, vectors and metadata (`document_id`, `filename`, `chunk_index`) are saved in a persistent ChromaDB collection that uses cosine distance.
4. **Retrieve** (`retrieval.py`): the question is embedded and the top-k closest chunks are fetched, optionally filtered by `document_id`.
5. **Answer** (`rag.py`): the chunks become a context block in a prompt that tells the model to answer only from the context. The response includes the sources, with filename, chunk index and distance.

## Workflows

A workflow is an ordered list of steps. Each step has an `id`, a `name`, a `type`, a `prompt` and, depending on its type, a few more fields:

| Type | What it does | Extra fields |
| --- | --- | --- |
| `llm` | Sends the rendered prompt to Gemini. (`prompt` is accepted as a legacy alias.) | `system_prompt`, `temperature` (0 to 2) |
| `rag` | Treats the rendered prompt as a question and answers it from the vector store. | `top_k` (default 5), `document_id` (optional) |

Prompts can use `{{variable}}` placeholders (`prompts.py`). Available variables:

- `{{input}}`: the input passed to `/execute`.
- `{{<step_id>.output}}`: the output of an earlier step.

An unknown variable fails the step with a clear error. The last step's output is the workflow's output.

```bash
curl -X POST localhost:8000/api/workflows -H 'content-type: application/json' -d '{
  "id": "summarize-then-ask",
  "name": "Summarize then ask",
  "steps": [
    {"id": "s1", "name": "Summarize", "type": "llm",
     "prompt": "Summarize in one line: {{input}}"},
    {"id": "s2", "name": "Look up", "type": "rag",
     "prompt": "What do the documents say about: {{s1.output}}"}
  ]
}'

curl -X POST localhost:8000/api/workflows/summarize-then-ask/execute \
  -H 'content-type: application/json' -d '{"input": "Vector databases"}'
```

Every run is saved in SQLite. `workflow_executions` holds the run, `workflow_step_executions` holds each step's input, output, status and error, and `workflow_rag_sources` holds the chunks each RAG step used.

## Database

- **SQLite** (`backend/ai_workbench.db`): tables `workflows`, `workflow_steps`, `workflow_executions`, `workflow_step_executions` and `workflow_rag_sources`. They are created on startup, and `workflow_steps` gets `top_k` and `document_id` columns added automatically if your database predates them.
- **ChromaDB** (`backend/chroma_db/`): collection `ai_workbench_documents`.

To start from scratch, stop the server and delete `ai_workbench.db` and `chroma_db/`.

## Troubleshooting

- **`python3 main.py` says it can't find `main.py`**: you are in the wrong directory. Run it from `backend/`.
- **`GEMINI_API_KEY was not found`**: create `backend/.env` from `.env.example` and fill it in.
- **`ModuleNotFoundError`**: activate the venv and run `pip install -r requirements.txt`.
- **`404 ... model ... no longer available`**: pick a current model in `GEMINI_MODEL`.
- **`503` or `504` from Gemini**: the model is overloaded. `llm.py` retries server errors 3 times and times out after 30s, so retry later or switch model.
- **Upload returns 400**: only UTF-8 `.txt` files are supported.
