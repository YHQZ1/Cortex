# Cortex

Cortex is a local RAG console for GitHub repositories. It ingests a repo, chunks the source files, stores metadata in Postgres, indexes embeddings in Qdrant, and answers questions with a local Ollama model.

It can run fully on your machine: GitHub fetching, background ingestion, vector search, answer generation, and the React console all sit behind Docker Compose, while Ollama runs on the host.

The core loop:

```text
GitHub repo
-> fetch files
-> filter and chunk source
-> store files/chunks in Postgres
-> embed chunks with Ollama
-> index vectors in Qdrant
-> retrieve relevant chunks with hybrid search
-> generate an answer with source previews
```

## Stack

| Area            | Technology                  |
| --------------- | --------------------------- |
| Web console     | React, Vite, TypeScript     |
| Styling         | Tailwind CSS v4             |
| API             | FastAPI                     |
| Background jobs | Celery                      |
| Database        | PostgreSQL                  |
| Broker/cache    | Redis                       |
| Vector database | Qdrant                      |
| Embeddings      | Ollama `nomic-embed-text`   |
| Generation      | Ollama, for example `llama3.1` |
| Chunking        | LangChain text splitters    |

## Prerequisites

- Docker or Docker Desktop
- Docker Compose
- Ollama running on the host machine

Pull the local models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

## Quickstart

Create your local environment file and pull the local models:

```bash
make setup
```

Start the full stack:

```bash
make up
```

Open the web console:

```text
http://localhost:5173
```

The API is available at:

```text
http://localhost:8000
```

## Local Ports

| Service     | Default URL / Port        |
| ----------- | ------------------------- |
| Web         | `http://localhost:5173`   |
| API         | `http://localhost:8000`   |
| Postgres    | `localhost:5433`          |
| Redis       | `localhost:6379`          |
| Qdrant HTTP | `http://localhost:6333`   |
| Qdrant gRPC | `localhost:6334`          |

`POSTGRES_PORT` defaults to `5433` to avoid conflicting with a host Postgres on `5432`. Inside Docker, services still use `postgres:5432`.

## Using Cortex

1. Choose an indexed GitHub owner and repo from the picker, or enable manual mode and enter a new `owner/repo`.
2. Click **Ingest repository**.
3. Wait for the ingestion job to finish.
4. Ask a repository question in **Repository** mode.
5. Switch to **General** mode for normal LLM questions that should not use repo context.
6. Watch the answer stream in.
7. Click a source card to inspect the exact retrieved chunk.

Repository mode is intentionally grounded. If the indexed codebase does not contain enough context, Cortex should say that instead of stretching into a generic answer.

## API Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `GET /health` | Basic API health |
| `GET /ready` | Checks Postgres, Redis, and Qdrant |
| `GET /setup` | Checks local setup, Ollama, embedding model, and LLM model |
| `POST /ingestions` | Queue repo ingestion |
| `GET /ingestions/{job_id}` | Check ingestion status |
| `GET /repositories` | List indexed repositories |
| `POST /repositories/{source_ref}/reindex` | Reindex an existing repository |
| `DELETE /repositories/{source_ref}` | Delete indexed repository metadata, chunks, and vectors |
| `POST /search` | Keyword search chunks |
| `POST /search/semantic` | Vector search chunks |
| `POST /search/hybrid` | Combined vector and keyword/path search |
| `POST /ask` | Full RAG answer |
| `POST /ask/stream` | Streaming RAG answer |
| `GET /chunks/{chunk_id}` | Preview a retrieved source chunk |

## Environment

Important values in `.env.example`:

```env
API_PORT=8000
WEB_PORT=5173
VITE_API_BASE_URL=http://localhost:8000

POSTGRES_PORT=5433
REDIS_PORT=6379
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334

OLLAMA_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
LLM_MODEL=llama3.1

GITHUB_TOKEN=
WORKER_CONCURRENCY=2
```

`GITHUB_TOKEN` is optional for public repositories, but useful if you hit GitHub rate limits or need private repository access later.

## Development

Run only infrastructure:

```bash
make infra
```

Run the full app stack:

```bash
make up
```

Build the web app locally:

```bash
cd web
npm install
npm run build
```

Stop services:

```bash
make down
```

Remove local volumes:

```bash
docker compose --profile app down -v
```

## Production-Style Compose

The default `docker-compose.yml` is optimized for development: the API code is bind-mounted and Uvicorn runs with reload.

For a closer-to-release local run, use the production-style Compose file. It builds the API and web images, skips source bind mounts, and runs Uvicorn without reload:

```bash
make prod-up
```

Stop it with:

```bash
make prod-down
```

## Project Layout

```text
cortex/
├── api/
│   ├── app/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── repositories/
│   │   ├── pipeline/
│   │   ├── db/
│   │   └── workers/
│   ├── Dockerfile
│   └── pyproject.toml
├── web/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── .env.example
└── README.md
```

## License

MIT
