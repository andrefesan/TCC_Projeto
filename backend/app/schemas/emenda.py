from pydantic import BaseModel
from typing import Optional


class EmendaResponse(BaseModel):
    id: int
    codigo_emenda: Optional[str] = None
    cod_autor: Optional[int] = None
    nome_autor: Optional[str] = None
    ano: int
    tipo_emenda: Optional[str] = None
    funcao_nome: Optional[str] = None
    subfuncao_nome: Optional[str] = None
    uf: Optional[str] = None
    localidade: Optional[str] = None
    valor_empenhado: float = 0
    valor_liquidado: float = 0
    valor_pago: float = 0
    partido: Optional[str] = None
    source_url: Optional[str] = None
    parlamentar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class EmendaListResponse(BaseModel):
    items: list[EmendaResponse]
    total: int
    page: int
    page_size: int
