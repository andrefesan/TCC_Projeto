from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_pipeline
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag.pipeline import RAGPipeline
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def processar_consulta(
    request: QueryRequest,
    db: Session = Depends(get_db),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Processa consulta em linguagem natural sobre emendas parlamentares.
    """
    try:
        resultado = await pipeline.processar(request.consulta, db)
        return QueryResponse(**resultado)
    except Exception as e:
        logger.error("erro_processar_consulta", erro=str(e), tipo=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
