# Cortex

Cortex is a production-minded RAG backend for turning code repositories into a searchable knowledge base.

The goal is simple: connect your source repositories, index their files, and ask questions like:

```text
Where did I implement rate limiting?
How do my services handle retries?
Which repos use JWT authentication?
Show me examples of my database migration pattern.
```

Cortex is being built as a real backend system first: FastAPI for the API, Postgres for durable state, Redis and Celery for background jobs, Qdrant for vector search, and Ollama for local embeddings and generation.

## Architecture

The planned backend has three main parts:

```text
Client
  |
  v
FastAPI API
  |
  |-- Postgres
  |     durable app state, jobs, repos, files, chunks, query logs
  |
  |-- Redis
  |     Celery broker, caching, rate limits, lightweight locks
  |
  |-- Celery workers
  |     repository ingestion, chunking, embedding, indexing
  |
  |-- Qdrant
  |     vector search over embedded code chunks
  |
  |-- Ollama
        local embedding and LLM generation provider
```

The API should stay lightweight. Expensive work such as repository fetching, chunking, embedding, and indexing should run in background workers.

## Target Stack

| Area            | Technology                                |
| --------------- | ----------------------------------------- |
| API             | FastAPI                                   |
| App server      | Uvicorn                                   |
| Database        | PostgreSQL                                |
| ORM             | SQLAlchemy 2.x                            |
| Migrations      | Alembic                                   |
| Queue           | Celery                                    |
| Broker/cache    | Redis                                     |
| Vector database | Qdrant                                    |
| Embeddings      | Ollama                                    |
| Generation      | Ollama                                    |
| RAG utilities   | LangChain, used selectively               |
| Packaging       | uv                                        |
| Deployment      | Docker Compose, then container deployment |

LangChain may be used for focused RAG utilities such as text splitting, prompt templates, and output parsing. Cortex should still own the application architecture, job lifecycle, database state, and retrieval pipeline.

## Local Infrastructure

### Prerequisites

- Docker or Docker Desktop
- Docker Compose
- Ollama, when embedding/generation work begins

### Configure Environment

Create a local environment file:

```bash
cp .env.example .env
```

Important local defaults:

```env
POSTGRES_PORT=5433
REDIS_PORT=6379
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
OLLAMA_URL=http://host.docker.internal:11434
```

`POSTGRES_PORT` defaults to `5433` locally to avoid conflicts with an existing Postgres installation on the host machine. Inside Docker, services still connect to Postgres through `postgres:5432`.

### Start Infrastructure

```bash
docker compose up -d
```

This starts:

- Postgres
- Redis
- Qdrant

Check status:

```bash
docker compose ps
```

Expected local ports:

| Service     | Host URL                |
| ----------- | ----------------------- |
| Postgres    | `localhost:5433`        |
| Redis       | `localhost:6379`        |
| Qdrant HTTP | `http://localhost:6333` |
| Qdrant gRPC | `localhost:6334`        |

### Stop Infrastructure

```bash
docker compose down
```

To remove local volumes too:

```bash
docker compose down -v
```

## Application Services

The future API and worker services are already represented in `docker-compose.yml`, but they are behind the `app` profile because the backend application code has not been scaffolded yet.

Once the API exists, the full stack will run with:

```bash
docker compose --profile app up -d
```

That will start:

- `api`
- `worker`
- `postgres`
- `redis`
- `qdrant`

## Planned Repository Structure

The project will start small and grow as the backend earns more structure.

```text
cortex/
├── api/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── db/
│   │   └── workers/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── docker-compose.yml
├── .env.example
└── README.md
```

CLI and web UI can be added later, after the backend ingestion and retrieval flow is solid.

## Design Principles

- Keep the API request lifecycle fast.
- Run ingestion and indexing through background jobs.
- Store canonical metadata in Postgres.
- Store vectors and searchable payloads in Qdrant.
- Make ingestion incremental with file hashes and commit tracking.
- Keep provider boundaries explicit for GitHub, embeddings, LLMs, and vector storage.
- Use LangChain as a utility, not as the whole application architecture.
- Prefer observable, testable pipeline steps over hidden chains.

## License

MIT
