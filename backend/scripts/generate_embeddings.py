"""Script de geração de embeddings para emendas e classificações."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal
from app.services.indexing.embedding_generator import EmbeddingGenerator
from app.services.indexing.index_manager import IndexManager
from app.config import settings
import structlog

logger = structlog.get_logger()


def main():
    parser = argparse.ArgumentParser(description="Gerar embeddings para emendas e classificações")
    parser.add_argument("--force", action="store_true",
                        help="Regenerar todos os embeddings (limpa os existentes)")
    args = parser.parse_args()

    logger.info("iniciando_geracao_embeddings",
                modelo=settings.EMBEDDING_MODEL,
                dimensoes=settings.EMBEDDING_DIMENSIONS,
                force=args.force)

    db = SessionLocal()
    generator = EmbeddingGenerator()

    try:
        if args.force:
            logger.info("limpando_embeddings_existentes")
            db.execute(text("UPDATE emendas SET embedding = NULL"))
            db.execute(text("UPDATE classificacao_orcamentaria SET embedding = NULL"))
            db.commit()
            logger.info("embeddings_limpos")

        # 1. Gerar embeddings para emendas
        logger.info("gerando_embeddings_emendas")
        generator.atualizar_emendas(db)

        # 2. Gerar embeddings para classificações orçamentárias
        logger.info("gerando_embeddings_classificacoes")
        generator.atualizar_classificacoes(db)

        # 3. Gerar embeddings para documentos (com observação preenchida)
        logger.info("gerando_embeddings_documentos")
        generator.atualizar_documentos(db)

        # 4. Gerar embeddings para favorecidos
        logger.info("gerando_embeddings_favorecidos")
        generator.atualizar_favorecidos(db)

        # 5. Verificar/criar índices HNSW (apenas PostgreSQL)
        is_sqlite = "sqlite" in str(settings.DATABASE_URL)
        if not is_sqlite:
            logger.info("verificando_indices_hnsw")
            IndexManager.criar_indices_hnsw(
                db, m=settings.HNSW_M, ef_construction=settings.HNSW_EF_CONSTRUCTION
            )
            status = IndexManager.verificar_indices(db)
            logger.info("embeddings_completo", indices=status["total"])
        else:
            logger.info("sqlite_detectado_indices_hnsw_ignorados")

    except Exception as e:
        logger.error("erro_embeddings", erro=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
