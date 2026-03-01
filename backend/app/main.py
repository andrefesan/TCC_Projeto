import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from app.config import settings
from app.database import init_db
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    logger.info("startup_iniciando", pid=os.getpid())
    init_db()
    logger.info("db_inicializado")

    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        files = list(static_dir.iterdir())
        logger.info("static_files", count=len(files),
                     has_index=any(f.name == "index.html" for f in files))
    else:
        logger.warning("static_dir_nao_existe", path=str(static_dir))

    yield
    logger.info("shutdown")


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
    else:
        @app.get("/")
        async def root():
            return JSONResponse({"status": "ok", "message": "API running, frontend not built"})

    return app


app = create_app()
