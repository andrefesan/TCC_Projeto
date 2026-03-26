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

    def __init__(self):
        self._sqlite_cache = None  # Cache emendas: (embedding_matrix, metadata_rows)
        self._sqlite_cache_favorecidos = None  # Cache favorecidos

    def _is_sqlite(self, db: Session) -> bool:
        return "sqlite" in str(db.bind.url)

    def _carregar_cache_sqlite(self, db: Session):
        """Carrega e cacheia a matriz de embeddings para busca batch."""
        if self._sqlite_cache is not None:
            return self._sqlite_cache

        logger.info("carregando_cache_embeddings_sqlite")
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

        embeddings = []
        metadata = []
        for r in rows:
            row_dict = dict(r._mapping)
            emb_str = row_dict.pop("embedding")
            try:
                emb = json.loads(emb_str)
                embeddings.append(emb)
                metadata.append(row_dict)
            except (json.JSONDecodeError, TypeError):
                continue

        emb_matrix = np.array(embeddings, dtype=np.float32)
        # Normalizar para cosine similarity via dot product
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        emb_matrix = emb_matrix / norms

        self._sqlite_cache = (emb_matrix, metadata)
        logger.info("cache_embeddings_carregado", total=len(metadata))
        return self._sqlite_cache

    def _buscar_sqlite(self, busca_vetorial: dict, db: Session,
                       limit: int = 20) -> List[dict]:
        """Busca vetorial batch em SQLite (cosine similarity via numpy matricial)."""
        emb_matrix, metadata = self._carregar_cache_sqlite(db)

        query_emb = np.array(busca_vetorial["embedding"], dtype=np.float32)
        query_norm = np.linalg.norm(query_emb)
        if query_norm > 0:
            query_emb = query_emb / query_norm

        # Cosine similarity batch: dot product com embeddings normalizados
        similarities = emb_matrix @ query_emb
        threshold = settings.SIMILARITY_THRESHOLD

        # Filtrar por threshold e ordenar
        mask = similarities >= threshold
        valid_indices = np.where(mask)[0]
        valid_sims = similarities[valid_indices]

        # Top-K por similaridade
        if len(valid_indices) > limit:
            top_k_idx = np.argsort(valid_sims)[-limit:][::-1]
            valid_indices = valid_indices[top_k_idx]
            valid_sims = valid_sims[top_k_idx]
        else:
            sort_idx = np.argsort(valid_sims)[::-1]
            valid_indices = valid_indices[sort_idx]
            valid_sims = valid_sims[sort_idx]

        scored = []
        for idx, sim in zip(valid_indices, valid_sims):
            row_dict = dict(metadata[idx])
            row_dict["similaridade"] = float(sim)
            scored.append(row_dict)

        logger.info("busca_vetorial_sqlite", termo=busca_vetorial.get("termo", ""),
                     resultados=len(scored))
        return scored

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

    # ----- Busca vetorial de favorecidos -----

    def _carregar_cache_favorecidos_sqlite(self, db: Session):
        """Carrega cache de embeddings dos favorecidos (SQLite)."""
        if self._sqlite_cache_favorecidos is not None:
            return self._sqlite_cache_favorecidos

        result = db.execute(text("""
            SELECT id, cpf_cnpj, nome, tipo_pessoa, uf, embedding
            FROM favorecidos
            WHERE embedding IS NOT NULL
        """))
        rows = result.fetchall()

        embeddings = []
        metadata = []
        for r in rows:
            row_dict = dict(r._mapping)
            emb_str = row_dict.pop("embedding")
            try:
                emb = json.loads(emb_str)
                embeddings.append(emb)
                metadata.append(row_dict)
            except (json.JSONDecodeError, TypeError):
                continue

        if not embeddings:
            self._sqlite_cache_favorecidos = (np.array([]), [])
            return self._sqlite_cache_favorecidos

        emb_matrix = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        emb_matrix = emb_matrix / norms

        self._sqlite_cache_favorecidos = (emb_matrix, metadata)
        logger.info("cache_favorecidos_carregado", total=len(metadata))
        return self._sqlite_cache_favorecidos

    def buscar_favorecidos(self, busca_vetorial: dict, db: Session,
                           limit: int = 20) -> List[dict]:
        """Busca favorecidos semanticamente similares por embedding.

        Args:
            busca_vetorial: dict com "termo" (str) e "embedding" (list[float])
            db: sessão do banco
            limit: máximo de resultados

        Returns:
            Lista de dicts com cpf_cnpj, nome, tipo_pessoa, uf, similaridade
        """
        if self._is_sqlite(db):
            return self._buscar_favorecidos_sqlite(busca_vetorial, db, limit)

        embedding = busca_vetorial["embedding"]
        threshold = settings.SIMILARITY_THRESHOLD

        sql = """
            SELECT id, cpf_cnpj, nome, tipo_pessoa, uf,
                   1 - (embedding <=> CAST(:emb AS vector)) AS similaridade
            FROM favorecidos
            WHERE embedding IS NOT NULL
              AND 1 - (embedding <=> CAST(:emb AS vector)) >= :threshold
            ORDER BY embedding <=> CAST(:emb AS vector)
            LIMIT :limit
        """
        result = db.execute(text(sql), {
            "emb": str(embedding),
            "threshold": threshold,
            "limit": limit,
        })
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("busca_vetorial_favorecidos", termo=busca_vetorial.get("termo", ""),
                     resultados=len(rows))
        return rows

    def _buscar_favorecidos_sqlite(self, busca_vetorial: dict, db: Session,
                                    limit: int = 20) -> List[dict]:
        """Busca vetorial de favorecidos em SQLite."""
        emb_matrix, metadata = self._carregar_cache_favorecidos_sqlite(db)

        if len(emb_matrix) == 0:
            return []

        query_emb = np.array(busca_vetorial["embedding"], dtype=np.float32)
        query_norm = np.linalg.norm(query_emb)
        if query_norm > 0:
            query_emb = query_emb / query_norm

        similarities = emb_matrix @ query_emb
        threshold = settings.SIMILARITY_THRESHOLD

        mask = similarities >= threshold
        valid_indices = np.where(mask)[0]
        valid_sims = similarities[valid_indices]

        if len(valid_indices) > limit:
            top_k_idx = np.argsort(valid_sims)[-limit:][::-1]
            valid_indices = valid_indices[top_k_idx]
            valid_sims = valid_sims[top_k_idx]
        else:
            sort_idx = np.argsort(valid_sims)[::-1]
            valid_indices = valid_indices[sort_idx]
            valid_sims = valid_sims[sort_idx]

        scored = []
        for idx, sim in zip(valid_indices, valid_sims):
            row_dict = dict(metadata[idx])
            row_dict["similaridade"] = float(sim)
            scored.append(row_dict)

        logger.info("busca_vetorial_favorecidos_sqlite",
                     termo=busca_vetorial.get("termo", ""),
                     resultados=len(scored))
        return scored
