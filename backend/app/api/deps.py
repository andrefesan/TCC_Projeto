from app.database import SessionLocal
from app.services.rag.pipeline import RAGPipeline

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
        _pipeline = RAGPipeline()
    return _pipeline
