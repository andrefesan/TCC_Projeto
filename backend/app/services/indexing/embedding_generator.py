from sqlalchemy.orm import Session
from sqlalchemy import text
import json
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
            emenda.get("partido", ""),
            emenda.get("tipo_emenda", ""),
            emenda.get("funcao_nome", ""),
            emenda.get("subfuncao_nome", ""),
            emenda.get("descricao", ""),
            emenda.get("localidade", ""),
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
            SELECT e.id, e.nome_autor, e.funcao_nome, e.subfuncao_nome,
                   e.descricao, e.uf, e.ano, e.localidade, e.tipo_emenda,
                   p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE e.embedding IS NULL
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("nenhuma_emenda_para_indexar")
            return

        textos = [self._compor_texto(dict(r._mapping)) for r in rows]
        ids = [r.id for r in rows]
        embeddings = self.gerar_embeddings_batch(textos)

        is_sqlite = "sqlite" in str(db.bind.url)
        for emenda_id, embedding in zip(ids, embeddings):
            emb_value = json.dumps(embedding.tolist()) if is_sqlite else embedding.tolist()
            db.execute(text("""
                UPDATE emendas SET embedding = :emb WHERE id = :id
            """), {"emb": emb_value, "id": emenda_id})

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

        is_sqlite = "sqlite" in str(db.bind.url)
        for classif_id, embedding in zip(ids, embeddings):
            emb_value = json.dumps(embedding.tolist()) if is_sqlite else embedding.tolist()
            db.execute(text("""
                UPDATE classificacao_orcamentaria SET embedding = :emb WHERE id = :id
            """), {"emb": emb_value, "id": classif_id})

        db.commit()
        logger.info("embeddings_classificacao_gerados", total=len(ids))

    def _compor_texto_documento(self, doc: dict) -> str:
        """Compõe texto representativo de um documento de emenda para embedding."""
        partes = [
            doc.get("observacao", ""),
            doc.get("favorecido_nome", ""),
            doc.get("funcao", ""),
            doc.get("subfuncao", ""),
            doc.get("elemento_despesa", ""),
        ]
        return " | ".join(p for p in partes if p and p.strip())

    def atualizar_documentos(self, db: Session):
        """Gera embeddings para documentos com observação preenchida."""
        result = db.execute(text("""
            SELECT id, observacao, favorecido_nome, funcao, subfuncao, elemento_despesa
            FROM documentos_emenda
            WHERE embedding IS NULL
              AND observacao IS NOT NULL AND observacao != ''
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("nenhum_documento_para_indexar")
            return

        textos = [self._compor_texto_documento(dict(r._mapping)) for r in rows]
        ids = [r.id for r in rows]
        embeddings = self.gerar_embeddings_batch(textos)

        is_sqlite = "sqlite" in str(db.bind.url)
        for doc_id, embedding in zip(ids, embeddings):
            emb_value = json.dumps(embedding.tolist()) if is_sqlite else embedding.tolist()
            db.execute(text("""
                UPDATE documentos_emenda SET embedding = :emb WHERE id = :id
            """), {"emb": emb_value, "id": doc_id})

        db.commit()
        logger.info("embeddings_documentos_gerados", total=len(ids))

    def _compor_texto_favorecido(self, fav: dict) -> str:
        """Compõe texto representativo de um favorecido para embedding."""
        partes = [
            fav.get("nome", ""),
            f"Tipo: {fav.get('tipo_pessoa', '')}",
            f"UF: {fav.get('uf', '')}",
        ]
        return " | ".join(p for p in partes if p and p.strip())

    def atualizar_favorecidos(self, db: Session):
        """Gera embeddings para todos os favorecidos sem embedding."""
        result = db.execute(text("""
            SELECT id, nome, tipo_pessoa, uf
            FROM favorecidos
            WHERE embedding IS NULL
              AND nome IS NOT NULL AND nome != '' AND nome != 'Sem informação'
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("nenhum_favorecido_para_indexar")
            return

        textos = [self._compor_texto_favorecido(dict(r._mapping)) for r in rows]
        ids = [r.id for r in rows]
        embeddings = self.gerar_embeddings_batch(textos)

        is_sqlite = "sqlite" in str(db.bind.url)
        for fav_id, embedding in zip(ids, embeddings):
            emb_value = json.dumps(embedding.tolist()) if is_sqlite else embedding.tolist()
            db.execute(text("""
                UPDATE favorecidos SET embedding = :emb WHERE id = :id
            """), {"emb": emb_value, "id": fav_id})

        db.commit()
        logger.info("embeddings_favorecidos_gerados", total=len(ids))
