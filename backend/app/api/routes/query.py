from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_pipeline
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag.pipeline import RAGPipeline

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def processar_consulta(
    request: QueryRequest,
    db: Session = Depends(get_db),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Processa consulta em linguagem natural sobre emendas parlamentares.

    Recebe uma pergunta do cidadão e retorna resposta fundamentada com:
    - Texto em linguagem acessível
    - Citações verificáveis de fontes governamentais
    - Dados brutos recuperados
    - Metadados (latência, modo de busca, entidades extraídas)
    """
    resultado = await pipeline.processar(request.consulta, db)
    return QueryResponse(**resultado)
