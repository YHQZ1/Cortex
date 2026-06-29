from fastapi import FastAPI

from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.ingestions import router as ingestions_router
from app.routes.search import router as search_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.include_router(health_router, tags=["health"])
    app.include_router(ingestions_router)
    app.include_router(search_router)

    return app


app = create_app()
