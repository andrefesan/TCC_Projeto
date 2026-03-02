from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline
import structlog

logger = structlog.get_logger()

# Singleton do pipeline RAG
_pipeline: RAGPipeline | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        try:
            _pipeline = RAGPipeline()
        except Exception as e:
            logger.error("erro_criar_pipeline", erro=str(e), tipo=type(e).__name__)
            raise
    return _pipeline
