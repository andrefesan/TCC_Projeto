from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    consulta: str = Field(..., min_length=3, max_length=500,
                          description="Pergunta em linguagem natural")


class QueryMetadata(BaseModel):
    latencia_ms: int
    entidades: dict
    modo: str
    num_resultados: int
    total_no_banco: int | None = None
    dados_completos: bool | None = None


class QueryResponse(BaseModel):
    resposta: str
    resumo: str | None = None
    fontes: list[str]
    dados: list[dict]
    metadata: QueryMetadata
    disclaimer: str | None = None
    sugestoes_followup: list[str] = []
    visualization_hint: str | None = None
