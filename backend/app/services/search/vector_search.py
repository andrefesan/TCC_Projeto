from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.config import settings
import structlog

logger = structlog.get_logger()


class VectorSearchService:
    """Busca vetorial via pgvector (similaridade cosseno)."""

    def buscar(self, busca_vetorial: dict, db: Session,
               limit: int = 20) -> List[dict]:
        """Busca emendas mais similares por embedding.

        Args:
            busca_vetorial: dict com "termo" (str) e "embedding" (list[float])
            db: sessão do banco
            limit: máximo de resultados

        Returns:
            Lista de dicts no mesmo formato do SQLSearchService
        """
        embedding = busca_vetorial["embedding"]
        threshold = settings.SIMILARITY_THRESHOLD

        sql = """
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano, e.tipo_emenda,
                   e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido,
                   1 - (e.embedding <=> CAST(:emb AS vector)) AS similaridade
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE e.embedding IS NOT NULL
              AND 1 - (e.embedding <=> CAST(:emb AS vector)) >= :threshold
            ORDER BY e.embedding <=> CAST(:emb AS vector)
            LIMIT :limit
        """

        result = db.execute(text(sql), {
            "emb": str(embedding),
            "threshold": threshold,
            "limit": limit,
        })
        rows = [dict(r._mapping) for r in result.fetchall()]

        logger.info("busca_vetorial", termo=busca_vetorial.get("termo", ""),
                     resultados=len(rows))
        return rows
