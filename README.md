# Cortex

Cortex is a local RAG console for GitHub repositories. It ingests a repo, chunks the source files, stores metadata in Postgres, indexes embeddings in Qdrant, and answers questions with a local Ollama model.

It runs on your machine: GitHub fetching, background ingestion, vector search, answer generation, and the React console run through Docker Compose, while Ollama runs on the host operating system.

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

- Docker Engine with Docker Compose, or Docker Desktop
- Ollama installed and running on the host machine
- Git, if you are cloning the repository

Install Ollama from `https://ollama.com/download`, then start it before running Cortex.

On macOS and Windows, the Ollama desktop app usually starts the local server automatically. On Linux, or if the server is not already running, start it manually:

```bash
ollama serve
```

Pull the local models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

## Compatibility

| Platform | Status | Notes |
| -------- | ------ | ----- |
| macOS with Docker Desktop | Supported | Recommended local path. Cortex containers call host Ollama through `host.docker.internal`. |
| Windows with Docker Desktop + WSL 2 backend | Supported | Run the commands from PowerShell, Windows Terminal, or WSL. Ollama must be reachable on the host at port `11434`. |
| Linux with Docker Engine | Supported | Compose maps `host.docker.internal` to Docker's host gateway. Requires a Docker version that supports `host-gateway`. |
| Linux with rootless Docker | Not fully verified | Networking to host Ollama may require setting `OLLAMA_URL` manually. |
| Remote server / VPS | Supported with setup | Install Ollama on the same host or point `OLLAMA_URL` to a reachable Ollama server. Expose ports carefully. |

Cortex expects Ollama to be reachable from inside the API and worker containers at:

```env
OLLAMA_URL=http://host.docker.internal:11434
```

If your Docker setup cannot resolve `host.docker.internal`, set `OLLAMA_URL` in `.env` to an address reachable from containers.

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

If you do not have `make`, run the same setup manually:

```bash
cp .env.example .env
ollama pull nomic-embed-text
ollama pull llama3.1
docker compose --profile app up -d --build
```

For PowerShell on Windows:

```powershell
Copy-Item .env.example .env
ollama pull nomic-embed-text
ollama pull llama3.1
docker compose --profile app up -d --build
```

Verify the stack:

```bash
curl http://localhost:8000/ready
curl http://localhost:8000/setup
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

1. Choose an indexed GitHub owner and repo from the picker, or enable manual mode and paste a GitHub repository URL.
2. Click **Ingest repository**.
3. Wait for the ingestion job to finish.
4. Ask a repository question in **Repository** mode.
5. Switch to **General** mode for normal LLM questions that should not use repo context.
6. Watch the answer stream in.
7. Click a source card to inspect the exact retrieved chunk.

Repository mode is intentionally grounded. If the indexed codebase does not contain enough context, Cortex should say that instead of stretching into a generic answer.

Manual repository input accepts these formats and sends clean `owner/repo` values to the backend:

```text
owner/repo
https://github.com/owner/repo
https://github.com/owner/repo.git
github.com/owner/repo
git@github.com:owner/repo.git
```

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

Without `make`:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml down
```

The production-style Compose file still expects Ollama to run on the host machine. It does not package Ollama or model files inside the Cortex containers.

## Troubleshooting

Check container health:

```bash
docker compose ps
curl http://localhost:8000/ready
curl http://localhost:8000/setup
```

If `/setup` says Ollama is not reachable:

```bash
ollama serve
ollama list
```

If the models are missing:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

If Linux containers cannot reach host Ollama, edit `.env` and set `OLLAMA_URL` to an address reachable from Docker containers.

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
