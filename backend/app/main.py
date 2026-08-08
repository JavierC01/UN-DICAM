from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.Core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API backend para DIC Tool: FastAPI, Celery, Redis y PostgreSQL.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    storage_dir = Path(settings.STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

    @app.get("/", tags=["Health"])
    def root() -> dict[str, str]:
        return {"message": "UN-DICAM API en linea"}

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return app


app = create_app()
