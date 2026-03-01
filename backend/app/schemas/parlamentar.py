from pydantic import BaseModel
from typing import Optional


class ParlamentarResponse(BaseModel):
    cod_autor: int
    nome: str
    partido: Optional[str] = None
    uf: Optional[str] = None
    url_foto: Optional[str] = None

    model_config = {"from_attributes": True}


class ParlamentarListResponse(BaseModel):
    items: list[ParlamentarResponse]
    total: int
    page: int
    page_size: int
