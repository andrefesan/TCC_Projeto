from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    consulta: str = Field(..., min_length=3, max_length=500,
                          description="Pergunta em linguagem natural")


class QueryMetadata(BaseModel):
    latencia_ms: int
    entidades: dict
    modo: str
    num_resultados: int


class QueryResponse(BaseModel):
    resposta: str
    fontes: list[str]
    dados: list[dict]
    metadata: QueryMetadata
