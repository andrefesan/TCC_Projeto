from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.search.sql_search import SQLSearchService
from app.services.search.vector_search import VectorSearchService
import structlog

logger = structlog.get_logger()


class HybridSearchService:
    """Combina busca SQL estruturada com busca vetorial semântica."""

    def __init__(self):
        self.sql_search = SQLSearchService()
        self.vector_search = VectorSearchService()

    def buscar(self, filtros_sql: dict, busca_vetorial: Optional[dict],
               db: Session, limit: int = 20) -> List[dict]:
        """Executa busca híbrida: SQL + vetorial com deduplicação.

        Args:
            filtros_sql: filtros estruturados para SQL
            busca_vetorial: dict com "termo" e "embedding" (ou None)
            db: sessão do banco
            limit: máximo de resultados

        Returns:
            Lista de dicts com resultados combinados e deduplicados
        """
        # Busca SQL
        dados_sql = self.sql_search.construir_e_executar(filtros_sql, db, limit)

        # Se não há busca vetorial ou SQL já retornou bastante, retorna só SQL
        if not busca_vetorial or len(dados_sql) >= limit:
            return dados_sql[:limit]

        # Busca vetorial complementar
        dados_vetoriais = self.vector_search.buscar(busca_vetorial, db, limit)

        # Combinar com deduplicação por id
        ids_existentes = {d["id"] for d in dados_sql}
        combinados = list(dados_sql)
        for dv in dados_vetoriais:
            if dv["id"] not in ids_existentes:
                combinados.append(dv)
                ids_existentes.add(dv["id"])

        logger.info("busca_hibrida",
                     sql_resultados=len(dados_sql),
                     vetorial_resultados=len(dados_vetoriais),
                     combinados=len(combinados))

        return combinados[:limit]
