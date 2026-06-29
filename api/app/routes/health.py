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
