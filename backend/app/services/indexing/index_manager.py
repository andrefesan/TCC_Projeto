from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class IndexManager:
    """Gerência de índices HNSW e outros índices do banco."""

    @staticmethod
    def criar_indices_hnsw(db: Session, m: int = 16, ef_construction: int = 200):
        """Cria ou recria índices HNSW para busca vetorial."""
        indices = [
            (
                "idx_emendas_embedding",
                "emendas",
                f"USING hnsw (embedding vector_cosine_ops) WITH (m = {m}, ef_construction = {ef_construction})",
            ),
            (
                "idx_classif_embedding",
                "classificacao_orcamentaria",
                f"USING hnsw (embedding vector_cosine_ops) WITH (m = {m}, ef_construction = {ef_construction})",
            ),
        ]

        for nome, tabela, spec in indices:
            # Verificar se índice existe
            result = db.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = :nome"
            ), {"nome": nome})

            if result.fetchone():
                logger.info("indice_ja_existe", nome=nome)
                continue

            logger.info("criando_indice", nome=nome, tabela=tabela)
            db.execute(text(f"CREATE INDEX {nome} ON {tabela} {spec}"))
            db.commit()
            logger.info("indice_criado", nome=nome)

    @staticmethod
    def verificar_indices(db: Session) -> dict:
        """Verifica status dos índices do banco."""
        result = db.execute(text("""
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """))
        indices = [dict(r._mapping) for r in result.fetchall()]
        logger.info("indices_verificados", total=len(indices))
        return {"indices": indices, "total": len(indices)}

    @staticmethod
    def set_hnsw_ef_search(db: Session, ef_search: int = 100):
        """Configura ef_search para queries HNSW (trade-off velocidade/recall)."""
        db.execute(text(f"SET hnsw.ef_search = {ef_search}"))
        logger.info("hnsw_ef_search_configurado", ef_search=ef_search)
