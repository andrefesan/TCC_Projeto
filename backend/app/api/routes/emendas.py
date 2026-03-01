from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.api.deps import get_db
from app.models.emenda import Emenda
from app.models.parlamentar import Parlamentar
from app.schemas.emenda import EmendaResponse, EmendaListResponse

router = APIRouter()


@router.get("/emendas", response_model=EmendaListResponse)
def listar_emendas(
    ano: Optional[int] = None,
    uf: Optional[str] = None,
    autor: Optional[str] = None,
    funcao: Optional[str] = None,
    partido: Optional[str] = None,
    tipo_emenda: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista emendas parlamentares com filtros opcionais e paginação."""
    query = db.query(Emenda).outerjoin(Parlamentar)

    if ano:
        query = query.filter(Emenda.ano == ano)
    if uf:
        query = query.filter(Emenda.uf == uf.upper())
    if autor:
        query = query.filter(Emenda.nome_autor.ilike(f"%{autor}%"))
    if funcao:
        query = query.filter(Emenda.funcao == funcao)
    if partido:
        query = query.filter(Parlamentar.partido == partido.upper())
    if tipo_emenda:
        query = query.filter(Emenda.tipo_emenda.ilike(f"%{tipo_emenda}%"))

    total = query.count()
    emendas = (
        query.order_by(Emenda.valor_empenhado.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for e in emendas:
        items.append(EmendaResponse(
            id=e.id,
            codigo_emenda=e.codigo_emenda,
            nome_autor=e.nome_autor,
            ano=e.ano,
            tipo_emenda=e.tipo_emenda,
            funcao_nome=e.funcao_nome,
            subfuncao_nome=e.subfuncao_nome,
            uf=e.uf,
            localidade=e.localidade,
            valor_empenhado=float(e.valor_empenhado or 0),
            valor_liquidado=float(e.valor_liquidado or 0),
            valor_pago=float(e.valor_pago or 0),
            partido=e.parlamentar.partido if e.parlamentar else None,
        ))

    return EmendaListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
