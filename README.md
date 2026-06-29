# Cortex

Cortex is a local RAG console for GitHub repositories. It ingests a repo, chunks the source files, stores metadata in Postgres, indexes embeddings in Qdrant, and answers questions with a local Ollama model.

The core loop:

```text
GitHub repo
-> fetch files
-> filter and chunk source
-> store files/chunks in Postgres
-> embed chunks with Ollama
-> index vectors in Qdrant
-> retrieve relevant chunks
-> generate an answer with sources
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

Create your local environment file:

```bash
cp .env.example .env
```

Start the full stack:

```bash
docker compose --profile app up -d --build
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
4. Ask a question.
5. Watch the answer stream in.
6. Click a source card to inspect the exact retrieved chunk.

## API Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `GET /health` | Basic API health |
| `GET /ready` | Checks Postgres, Redis, and Qdrant |
| `POST /ingestions` | Queue repo ingestion |
| `GET /ingestions/{job_id}` | Check ingestion status |
| `GET /repositories` | List indexed repositories |
| `POST /search` | Keyword search chunks |
| `POST /search/semantic` | Vector search chunks |
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
docker compose up -d
```

Run the full app stack:

```bash
docker compose --profile app up -d --build
```

Build the web app locally:

```bash
cd web
npm install
npm run build
```

Stop services:

```bash
docker compose --profile app down
```

Remove local volumes:

```bash
docker compose --profile app down -v
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
├── .env.example
└── README.md
```

## License

MIT
