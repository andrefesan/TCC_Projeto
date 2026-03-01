from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.models.parlamentar import Parlamentar
from app.schemas.parlamentar import ParlamentarResponse, ParlamentarListResponse

router = APIRouter()


@router.get("/parlamentares", response_model=ParlamentarListResponse)
def listar_parlamentares(
    nome: Optional[str] = None,
    partido: Optional[str] = None,
    uf: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista parlamentares com filtros opcionais e paginação."""
    query = db.query(Parlamentar)

    if nome:
        query = query.filter(Parlamentar.nome.ilike(f"%{nome}%"))
    if partido:
        query = query.filter(Parlamentar.partido == partido.upper())
    if uf:
        query = query.filter(Parlamentar.uf == uf.upper())

    total = query.count()
    parlamentares = (
        query.order_by(Parlamentar.nome)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [ParlamentarResponse.model_validate(p) for p in parlamentares]

    return ParlamentarListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
