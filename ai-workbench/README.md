# AI Workbench

A learning project for building AI applications on top of Google Gemini. It has a FastAPI backend and a Next.js frontend, and covers four things:

- **Chat**: multi-turn chat with Gemini, streamed token by token, with an editable system prompt and temperature.
- **Embeddings**: turn text into vectors with `gemini-embedding-001`.
- **RAG**: upload `.txt` documents, chunk and embed them into ChromaDB, then ask questions grounded in those documents.
- **RAG evaluation**: score the RAG pipeline on a fixed set of test questions and compare runs, to see whether a change (chunk size, top K) helped.
- **Learning labs**: three interactive pages that show what happens inside RAG: a chunking lab, an embeddings visualizer and a prompt viewer.
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
| POST | `/api/chat` | `{"message": "..."}` returns `{"response": "..."}`. Single turn, no history. |
| POST | `/api/chat/stream` | Multi-turn chat. Body: `{"messages": [{"role": "user" \| "assistant", "content": "..."}], "system_prompt": "...", "temperature": 0.7}`. The last message must be from the user. The reply streams back as Server-Sent Events. See "Chat" below. |
| POST | `/api/embeddings` | `{"text": "..."}` returns the embedding vector and its dimensions |
| POST | `/api/documents/upload` | Multipart `file` (`.txt`, UTF-8). Chunks it (query params `chunk_size`, default 500, and `chunk_overlap`, default 50), embeds each chunk and stores them in ChromaDB. |
| POST | `/api/documents/search` | `{"query": "...", "top_k": 5}` returns the nearest chunks |
| POST | `/api/documents/ask` | `{"question": "...", "top_k": 5, "document_id": null, "include_prompt": false}` returns a RAG answer with its sources. Set `document_id` to restrict retrieval to one document. Set `include_prompt` to also get the exact prompt sent to the model, split into `system`, `context`, `question` and `full`. |
| POST | `/api/evaluations/run` | Run a set of test questions through RAG and score them. See "RAG evaluation" below. |
| GET | `/api/evaluations/runs` | List past runs with their scores |
| GET | `/api/evaluations/runs/{id}` | One run with per-question results |
| DELETE | `/api/evaluations/runs/{id}` | Delete a run |
| POST | `/api/lab/chunk` | `{"text": "...", "chunk_size": 500, "chunk_overlap": 50}` returns the chunks with their character offsets. No AI call is made. |
| POST | `/api/lab/similarity` | `{"texts": ["...", "..."]}` (2 to 12 texts) returns the cosine-similarity matrix and 2D PCA coordinates. Calls the embedding model once per text. |
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

## Chat

The chat page (`/chat`) is a multi-turn chatbot with streaming.

- **Memory:** the model itself remembers nothing. The server is stateless, and the browser sends the whole conversation with every request. The conversation is also saved in the browser's `localStorage`, so a refresh keeps it.
- **Streaming:** `POST /api/chat/stream` replies with `text/event-stream`. Each event is one line of JSON:
  - `data: {"text": "..."}`: a piece of the answer, sent many times.
  - `data: {"done": true, "dropped": 0}`: sent once at the end. `dropped` is how many old messages were left out.
  - `data: {"error": "..."}`: sent instead if the model call fails.
- **Context trimming** (`conversation.py`): a model can only read so much, so when the history passes a budget of 12,000 characters (about 3,000 tokens) the oldest messages are left out of the request. The page tells the user when this happens. The budget is a simple character count, not a real token count.
- **Controls:** Stop cancels a running answer, Regenerate asks again for the last answer, and New chat clears the conversation. Settings lets you change the system prompt and temperature.

```bash
curl -N -X POST localhost:8000/api/chat/stream -H 'content-type: application/json' -d '{
  "messages": [
    {"role": "user", "content": "My name is Sam."},
    {"role": "assistant", "content": "Nice to meet you, Sam."},
    {"role": "user", "content": "What is my name?"}
  ]
}'
```

## RAG evaluation

A RAG demo that works on one question proves little. The evaluation page (`/evaluation`) runs a fixed set of test questions through the pipeline and gives you scores, so you can change one thing and see whether it helped.

Each test question has three parts:

- `question`: what to ask.
- `evidence`: a phrase that must appear in the chunk holding the answer. Leave it empty for a question the document cannot answer.
- `reference_answer`: what a correct answer says (used by the AI judge).

Metrics:

| Metric | Mode | Meaning |
| --- | --- | --- |
| Hit rate | both | Share of questions where a chunk containing the evidence was retrieved in the top K. |
| MRR | both | Mean of 1 / rank of that chunk (1.0 means it is always first, 0 means never found). |
| Correctness | `full` | An AI judge says the answer agrees with the reference answer. |
| Faithfulness | `full` | An AI judge says every claim in the answer is supported by the retrieved chunks. |

Retrieval metrics only count questions that have `evidence`. Questions that error are left out of every average and are shown with their error.

Two modes:

- **`retrieval`** only embeds each question and checks what comes back. It is fast and makes no generation calls. Start here: if the right chunk is not retrieved, no prompt can fix the answer.
- **`full`** also generates each answer and has the judge grade it. That is 2 model calls per question.

**Rate limits:** Gemini free-tier keys allow about 5 generation calls a minute, so a `full` run of more than a couple of questions takes minutes. `llm.py` waits for the delay the API asks for and retries when it gets a 429. A run is limited to 20 questions, and 2 are evaluated at a time.

Every run is stored in SQLite (`eval_runs` and `eval_results`). The page's history table shows the runs side by side and highlights the best score in each column.

A good first experiment: upload `docs/test.txt` at chunk size 500 and again at chunk size 120, run the sample questions in `retrieval` mode with top K 1 for each, and compare. On the sample set, small chunks scored lower because they cut the answer apart.

```bash
curl -X POST localhost:8000/api/evaluations/run -H 'content-type: application/json' -d '{
  "label": "chunk 500, top 3",
  "mode": "retrieval",
  "top_k": 3,
  "document_id": null,
  "cases": [
    {"question": "What do vector databases do?",
     "reference_answer": "They store embeddings and search for similar information.",
     "evidence": "store embeddings"}
  ]
}'
```

## Learning labs

Open these from the nav bar in the frontend. They are meant for beginners, so each page explains the idea before showing it.

| Page | URL | What it shows |
| --- | --- | --- |
| Chunking Lab | `/lab/chunking` | Paste text and move the chunk size and overlap sliders. The text is colored by chunk, and overlapping text is underlined. Runs instantly and makes no AI calls. |
| Embeddings Visualizer | `/lab/embeddings` | Enter a few texts, one per line. Each is embedded with Gemini, then shown on a 2D map plus a similarity heatmap, so you can see that "kitten" is closer to "cat" than to "car". Includes presets, such as one with two meanings of "bank". |
| Show the prompt | `/` (after asking a question) | Below every RAG answer, the exact prompt sent to the model, split into instructions, retrieved context and your question. It shows that RAG is only a normal LLM call with extra text pasted in. |

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

- **SQLite** (`backend/ai_workbench.db`): tables `workflows`, `workflow_steps`, `workflow_executions`, `workflow_step_executions`, `workflow_rag_sources`, `eval_runs` and `eval_results`. They are created on startup, and `workflow_steps` gets `top_k` and `document_id` columns added automatically if your database predates them.
- **ChromaDB** (`backend/chroma_db/`): collection `ai_workbench_documents`.

To start from scratch, stop the server and delete `ai_workbench.db` and `chroma_db/`.

## Troubleshooting

- **`python3 main.py` says it can't find `main.py`**: you are in the wrong directory. Run it from `backend/`.
- **`GEMINI_API_KEY was not found`**: create `backend/.env` from `.env.example` and fill it in.
- **`ModuleNotFoundError`**: activate the venv and run `pip install -r requirements.txt`.
- **`404 ... model ... no longer available`**: pick a current model in `GEMINI_MODEL`.
- **`503` or `504` from Gemini**: the model is overloaded. `llm.py` retries server errors 3 times and times out after 30s, so retry later or switch model.
- **Upload returns 400**: only UTF-8 `.txt` files are supported.
