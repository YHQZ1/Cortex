COMPOSE := docker compose
DEV_COMPOSE := $(COMPOSE) --profile app
PROD_COMPOSE := $(COMPOSE) -f docker-compose.prod.yml

.PHONY: help setup up down restart logs ps infra infra-down prod-up prod-down prod-logs api-compile web-build

help:
	@echo "Cortex commands"
	@echo "  make setup       Create .env and pull local Ollama models"
	@echo "  make up          Build and start the dev stack"
	@echo "  make down        Stop the dev stack"
	@echo "  make logs        Tail dev stack logs"
	@echo "  make infra       Start only Postgres, Redis, and Qdrant"
	@echo "  make prod-up     Build and start the production-style stack"
	@echo "  make prod-down   Stop the production-style stack"
	@echo "  make api-compile Compile-check the FastAPI app inside Docker"
	@echo "  make web-build   Build the React app locally"

setup:
	@cp -n .env.example .env || true
	ollama pull nomic-embed-text
	ollama pull llama3.1

up:
	$(DEV_COMPOSE) up -d --build

down:
	$(DEV_COMPOSE) down

restart:
	$(DEV_COMPOSE) restart

logs:
	$(DEV_COMPOSE) logs -f

ps:
	$(COMPOSE) ps

infra:
	$(COMPOSE) up -d postgres redis qdrant

infra-down:
	$(COMPOSE) down

prod-up:
	$(PROD_COMPOSE) up -d --build

prod-down:
	$(PROD_COMPOSE) down

prod-logs:
	$(PROD_COMPOSE) logs -f

api-compile:
	$(COMPOSE) exec api python -m compileall app

web-build:
	cd web && npm run build
