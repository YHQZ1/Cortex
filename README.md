# Cortex

A local RAG engine that turns your GitHub repos into a queryable knowledge base. Ask questions about your own code in natural language — get answers with file context, repo references, and actual code snippets. Runs fully offline.

```
$ cortex query "how did I implement rate limiting?"

> Found in: flintlk/ratelimit/limiter.go

  You used a token bucket approach backed by an in-memory atomic counter
  with a configurable refill interval. The core logic lives in Limiter.Allow()
  which checks remaining tokens before decrementing.

  [flintlk/ratelimit/limiter.go · lines 42–67]
```

---

## How it works

```
GitHub API
    └── pulls READMEs + source files from all your repos
            │
            ▼
    Text Splitter (LangChain)
            │  chunks files by size with overlap
            ▼
    Ollama (nomic-embed-text)
            │  converts each chunk to a vector
            ▼
    Qdrant (vector database)
            │  stores vectors + metadata (repo, file, line range)
            ▼
    Query CLI / Web UI
            │  embeds your question → finds top-k similar chunks
            │  → sends context to qwen2.5-coder → returns answer
            ▼
         Answer
```

No cloud. No API keys. No cost.

---

## Stack

| Layer            | Technology                                 |
| ---------------- | ------------------------------------------ |
| Backend          | FastAPI                                    |
| Vector DB        | Qdrant                                     |
| Embeddings       | `nomic-embed-text` via Ollama              |
| LLM              | `qwen2.5-coder:7b` via Ollama              |
| Text splitting   | LangChain `RecursiveCharacterTextSplitter` |
| Frontend         | React + TypeScript + Tailwind v4           |
| GitHub ingestion | PyGithub                                   |
| Orchestration    | Docker Compose                             |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Ollama](https://ollama.com/download) installed and running
- Python 3.11+
- Node.js 20+
- A GitHub personal access token (read-only scope is enough)

---

## Setup

**1. Pull the models**

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5-coder:7b
```

**2. Clone and configure**

```bash
git clone https://github.com/yourhandle/cortex
cd cortex
cp .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=your_github_pat_here
GITHUB_USERNAME=your_github_username
```

**3. Start Qdrant**

```bash
docker compose up -d
```

**4. Install backend dependencies**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**5. Index your repos**

```bash
python indexer.py
```

This pulls all your public repos, chunks the files, embeds them, and stores everything in Qdrant. Takes a few minutes depending on how many repos you have.

**6. Start the backend**

```bash
uvicorn main:app --reload --port 8000
```

**7. Start the frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## CLI

```bash
cd backend
python cli.py query "where did I use exponential backoff?"
python cli.py query "what's my pattern for gRPC error handling?"
python cli.py reindex --repo flintlk/ratelimit
```

---

## Project structure

```
cortex/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── indexer.py           # GitHub ingestion + embedding pipeline
│   ├── retriever.py         # Qdrant query logic
│   ├── cli.py               # CLI entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── api/
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## Configuration

| Variable          | Default                  | Description                |
| ----------------- | ------------------------ | -------------------------- |
| `GITHUB_TOKEN`    | —                        | GitHub PAT (read scope)    |
| `GITHUB_USERNAME` | —                        | Your GitHub handle         |
| `QDRANT_HOST`     | `localhost`              | Qdrant host                |
| `QDRANT_PORT`     | `6333`                   | Qdrant port                |
| `OLLAMA_HOST`     | `http://localhost:11434` | Ollama base URL            |
| `EMBED_MODEL`     | `nomic-embed-text`       | Embedding model            |
| `LLM_MODEL`       | `qwen2.5-coder:7b`       | Generation model           |
| `TOP_K`           | `5`                      | Chunks retrieved per query |

---

## Reindexing

Cortex doesn't auto-sync. Run the indexer manually when you want to pull in new repos or changes:

```bash
python indexer.py              # full reindex
python indexer.py --repo REPO  # single repo
```

---

## License

MIT
