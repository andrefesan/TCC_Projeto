from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import json
import numpy as np
from app.config import settings
import structlog

logger = structlog.get_logger()


class VectorSearchService:
    """Busca vetorial via pgvector ou fallback em Python para SQLite."""

    def _is_sqlite(self, db: Session) -> bool:
        return "sqlite" in str(db.bind.url)

    def _buscar_sqlite(self, busca_vetorial: dict, db: Session,
                       limit: int = 20) -> List[dict]:
        """Busca vetorial em Python para SQLite (cosine similarity via numpy)."""
        query_embedding = np.array(busca_vetorial["embedding"], dtype=np.float32)
        threshold = settings.SIMILARITY_THRESHOLD

        result = db.execute(text("""
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano, e.tipo_emenda,
                   e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   e.embedding,
                   p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE e.embedding IS NOT NULL
        """))
        rows = result.fetchall()

        scored = []
        for r in rows:
            row_dict = dict(r._mapping)
            emb_str = row_dict.pop("embedding")
            try:
                emb = np.array(json.loads(emb_str), dtype=np.float32)
            except (json.JSONDecodeError, TypeError):
                continue
            sim = float(np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-10
            ))
            if sim >= threshold:
                row_dict["similaridade"] = sim
                scored.append(row_dict)

        scored.sort(key=lambda x: x["similaridade"], reverse=True)
        logger.info("busca_vetorial_sqlite", termo=busca_vetorial.get("termo", ""),
                     resultados=len(scored[:limit]))
        return scored[:limit]

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
        if self._is_sqlite(db):
            return self._buscar_sqlite(busca_vetorial, db, limit)

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
