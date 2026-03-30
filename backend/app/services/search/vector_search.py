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
        self._sqlite_cache_documentos = None  # Cache documentos_emenda

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

    # ----- Busca vetorial em documentos de emenda (observações) -----

    def _carregar_cache_documentos_sqlite(self, db: Session):
        """Carrega cache de embeddings dos documentos de emenda (SQLite)."""
        if self._sqlite_cache_documentos is not None:
            return self._sqlite_cache_documentos

        logger.info("carregando_cache_documentos_sqlite")
        result = db.execute(text("""
            SELECT d.id, d.emenda_id, d.observacao, d.embedding
            FROM documentos_emenda d
            WHERE d.embedding IS NOT NULL
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
            self._sqlite_cache_documentos = (np.array([]), [])
            return self._sqlite_cache_documentos

        emb_matrix = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        emb_matrix = emb_matrix / norms

        self._sqlite_cache_documentos = (emb_matrix, metadata)
        logger.info("cache_documentos_carregado", total=len(metadata))
        return self._sqlite_cache_documentos

    def _buscar_documentos_sqlite(self, busca_vetorial: dict, db: Session,
                                   limit: int = 20) -> List[dict]:
        """Busca vetorial em documentos de emenda (SQLite).

        Encontra documentos cuja observação é semanticamente similar à consulta,
        depois retorna as emendas-pai no formato padrão.
        """
        emb_matrix, metadata = self._carregar_cache_documentos_sqlite(db)

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

        # Top-K documentos por similaridade (buscar mais para deduplicar por emenda)
        fetch_limit = limit * 5
        if len(valid_indices) > fetch_limit:
            top_k_idx = np.argsort(valid_sims)[-fetch_limit:][::-1]
            valid_indices = valid_indices[top_k_idx]
            valid_sims = valid_sims[top_k_idx]
        else:
            sort_idx = np.argsort(valid_sims)[::-1]
            valid_indices = valid_indices[sort_idx]
            valid_sims = valid_sims[sort_idx]

        # Agrupar por emenda_id, manter maior similaridade e observação
        emenda_best = {}  # emenda_id -> (similaridade, observacao)
        for idx, sim in zip(valid_indices, valid_sims):
            doc = metadata[idx]
            eid = doc["emenda_id"]
            if eid not in emenda_best or sim > emenda_best[eid][0]:
                emenda_best[eid] = (float(sim), doc.get("observacao", ""))

        if not emenda_best:
            return []

        # Buscar emendas-pai
        emenda_ids = list(emenda_best.keys())[:limit]
        placeholders = ",".join(f":id{i}" for i in range(len(emenda_ids)))
        params = {f"id{i}": eid for i, eid in enumerate(emenda_ids)}

        result = db.execute(text(f"""
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano, e.tipo_emenda,
                   e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE e.id IN ({placeholders})
        """), params)

        scored = []
        for r in result.fetchall():
            row_dict = dict(r._mapping)
            eid = row_dict["id"]
            sim, obs = emenda_best.get(eid, (0.0, ""))
            row_dict["similaridade"] = sim
            row_dict["doc_observacao"] = obs
            scored.append(row_dict)

        # Ordenar por similaridade
        scored.sort(key=lambda x: x["similaridade"], reverse=True)

        logger.info("busca_vetorial_documentos_sqlite",
                     termo=busca_vetorial.get("termo", "")[:50],
                     resultados=len(scored))
        return scored

    def buscar_documentos(self, busca_vetorial: dict, db: Session,
                          limit: int = 20) -> List[dict]:
        """Busca emendas via similaridade semântica nos documentos de despesa.

        Busca em documentos_emenda.embedding (gerado a partir de observação,
        favorecido, função, subfunção) e retorna as emendas-pai no formato
        padrão compatível com buscar().

        Args:
            busca_vetorial: dict com "termo" (str) e "embedding" (list[float])
            db: sessão do banco
            limit: máximo de resultados

        Returns:
            Lista de dicts no mesmo formato do buscar(), com campo adicional
            doc_observacao contendo a observação do documento encontrado.
        """
        if self._is_sqlite(db):
            return self._buscar_documentos_sqlite(busca_vetorial, db, limit)

        embedding = busca_vetorial["embedding"]
        threshold = settings.SIMILARITY_THRESHOLD

        sql = """
            WITH docs_ranked AS (
                SELECT d.emenda_id,
                       d.observacao AS doc_observacao,
                       1 - (d.embedding <=> CAST(:emb AS vector)) AS similaridade,
                       ROW_NUMBER() OVER (
                           PARTITION BY d.emenda_id
                           ORDER BY d.embedding <=> CAST(:emb AS vector)
                       ) AS rn
                FROM documentos_emenda d
                WHERE d.embedding IS NOT NULL
                  AND 1 - (d.embedding <=> CAST(:emb AS vector)) >= :threshold
            )
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano, e.tipo_emenda,
                   e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido,
                   dr.similaridade,
                   dr.doc_observacao
            FROM docs_ranked dr
            JOIN emendas e ON e.id = dr.emenda_id
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE dr.rn = 1
            ORDER BY dr.similaridade DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), {
            "emb": str(embedding),
            "threshold": threshold,
            "limit": limit,
        })
        rows = [dict(r._mapping) for r in result.fetchall()]

        logger.info("busca_vetorial_documentos", termo=busca_vetorial.get("termo", "")[:50],
                     resultados=len(rows))
        return rows
