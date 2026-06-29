from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.ask import router as ask_router
from app.routes.health import router as health_router
from app.routes.ingestions import router as ingestions_router
from app.routes.repositories import router as repositories_router
from app.routes.search import router as search_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, tags=["health"])
    app.include_router(ingestions_router)
    app.include_router(repositories_router)
    app.include_router(ask_router)
    app.include_router(search_router)

    return app


app = create_app()
