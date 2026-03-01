from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np
from app.config import settings
import structlog

logger = structlog.get_logger()


class EmbeddingGenerator:
    """Gera embeddings para emendas e classificações orçamentárias."""

    def __init__(self):
        self._model = None
        self.batch_size = settings.EMBEDDING_BATCH_SIZE

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("carregando_modelo_embeddings", model=settings.EMBEDDING_MODEL)
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def _compor_texto(self, emenda: dict) -> str:
        """Compõe texto representativo de uma emenda para embedding."""
        partes = [
            emenda.get("nome_autor", ""),
            emenda.get("funcao_nome", ""),
            emenda.get("subfuncao_nome", ""),
            emenda.get("descricao", ""),
            f"UF: {emenda.get('uf', '')}",
            f"Ano: {emenda.get('ano', '')}",
        ]
        return " | ".join(p for p in partes if p and p.strip())

    def gerar_embeddings_batch(self, textos: list[str]) -> np.ndarray:
        """Gera embeddings em batch."""
        logger.info("gerando_embeddings", total=len(textos),
                     batch_size=self.batch_size)
        embeddings = self.model.encode(
            textos,
            batch_size=self.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return embeddings

    def atualizar_emendas(self, db: Session):
        """Gera embeddings para todas as emendas sem embedding."""
        result = db.execute(text("""
            SELECT id, nome_autor, funcao_nome, subfuncao_nome, descricao, uf, ano
            FROM emendas WHERE embedding IS NULL
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("nenhuma_emenda_para_indexar")
            return

        textos = [self._compor_texto(dict(r._mapping)) for r in rows]
        ids = [r.id for r in rows]
        embeddings = self.gerar_embeddings_batch(textos)

        for emenda_id, embedding in zip(ids, embeddings):
            db.execute(text("""
                UPDATE emendas SET embedding = :emb WHERE id = :id
            """), {"emb": embedding.tolist(), "id": emenda_id})

        db.commit()
        logger.info("embeddings_gerados", total=len(ids))

    def atualizar_classificacoes(self, db: Session):
        """Gera embeddings para classificações orçamentárias."""
        result = db.execute(text("""
            SELECT id, funcao_nome, subfuncao_nome, programa_nome, descricao
            FROM classificacao_orcamentaria WHERE embedding IS NULL
        """))
        rows = result.fetchall()

        if not rows:
            return

        textos = [
            f"{r.funcao_nome} {r.subfuncao_nome} {r.programa_nome} {r.descricao}"
            for r in rows
        ]
        ids = [r.id for r in rows]
        embeddings = self.gerar_embeddings_batch(textos)

        for classif_id, embedding in zip(ids, embeddings):
            db.execute(text("""
                UPDATE classificacao_orcamentaria SET embedding = :emb WHERE id = :id
            """), {"emb": embedding.tolist(), "id": classif_id})

        db.commit()
        logger.info("embeddings_classificacao_gerados", total=len(ids))
