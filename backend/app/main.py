import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Transparência Fiscal API",
        description="API para consulta inteligente de emendas parlamentares",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS: permite origens de produção e desenvolvimento
    origins = [
        settings.FRONTEND_URL,
        "http://localhost:5173",
    ]
    if settings.PRODUCTION_URL:
        origins.append(settings.PRODUCTION_URL)
        # Também permite com e sem www
        if not settings.PRODUCTION_URL.startswith("https://www."):
            origins.append(settings.PRODUCTION_URL.replace("https://", "https://www."))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api")

    # Serve frontend static files (built by Dockerfile)
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
