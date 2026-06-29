from typing import Any

import asyncpg
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from app.config import Settings, get_settings

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/ready")
async def ready(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    checks = {
        "postgres": await _check_postgres(settings),
        "redis": await _check_redis(settings),
        "qdrant": await _check_qdrant(settings),
    }

    is_ready = all(check["ok"] for check in checks.values())
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}


@router.get("/setup")
async def setup(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    checks = {
        "api": {"ok": True},
        "postgres": await _check_postgres(settings),
        "redis": await _check_redis(settings),
        "qdrant": await _check_qdrant(settings),
        "ollama": await _check_ollama(settings),
    }
    checks["embedding_model"] = _check_model(
        checks["ollama"],
        model_name=settings.embedding_model,
    )
    checks["llm_model"] = _check_model(
        checks["ollama"],
        model_name=settings.llm_model,
    )

    is_ready = all(check["ok"] for check in checks.values())
    return {
        "status": "ready" if is_ready else "needs_setup",
        "checks": checks,
        "commands": {
            "embedding_model": f"ollama pull {settings.embedding_model}",
            "llm_model": f"ollama pull {settings.llm_model}",
        },
    }


async def _check_postgres(settings: Settings) -> dict[str, Any]:
    try:
        connection = await asyncpg.connect(
            settings.asyncpg_url,
            timeout=settings.readiness_timeout_seconds,
        )
        try:
            await connection.execute("SELECT 1")
        finally:
            await connection.close()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


async def _check_redis(settings: Settings) -> dict[str, Any]:
    client = Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=settings.readiness_timeout_seconds,
        socket_timeout=settings.readiness_timeout_seconds,
    )
    try:
        await client.ping()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}
    finally:
        await client.aclose()


async def _check_qdrant(settings: Settings) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=settings.readiness_timeout_seconds) as client:
            response = await client.get(f"{settings.qdrant_url.rstrip('/')}/readyz")
            response.raise_for_status()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


async def _check_ollama(settings: Settings) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=settings.readiness_timeout_seconds) as client:
            response = await client.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        models = response.json().get("models", [])
        model_names = sorted(
            {
                name
                for model in models
                for name in (model.get("name"), model.get("model"))
                if isinstance(name, str)
            }
        )
        return {"ok": True, "url": settings.ollama_url, "models": model_names}
    except Exception as exc:
        return {"ok": False, "url": settings.ollama_url, "error": type(exc).__name__, "models": []}


def _check_model(ollama_check: dict[str, Any], *, model_name: str) -> dict[str, Any]:
    models = ollama_check.get("models", [])
    model_aliases = {model_name, f"{model_name}:latest"}
    is_installed = ollama_check["ok"] and any(model in model_aliases for model in models)
    return {
        "ok": is_installed,
        "name": model_name,
        "error": None if is_installed else "ModelNotInstalled",
    }
