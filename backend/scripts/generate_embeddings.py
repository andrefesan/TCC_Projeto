"""Script de geração de embeddings para emendas e classificações."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.indexing.embedding_generator import EmbeddingGenerator
from app.services.indexing.index_manager import IndexManager
from app.config import settings
import structlog

logger = structlog.get_logger()


def main():
    logger.info("iniciando_geracao_embeddings",
                modelo=settings.EMBEDDING_MODEL,
                dimensoes=settings.EMBEDDING_DIMENSIONS)

    db = SessionLocal()
    generator = EmbeddingGenerator()

    try:
        # 1. Gerar embeddings para emendas
        logger.info("gerando_embeddings_emendas")
        generator.atualizar_emendas(db)

        # 2. Gerar embeddings para classificações orçamentárias
        logger.info("gerando_embeddings_classificacoes")
        generator.atualizar_classificacoes(db)

        # 3. Verificar/criar índices HNSW
        logger.info("verificando_indices_hnsw")
        IndexManager.criar_indices_hnsw(
            db, m=settings.HNSW_M, ef_construction=settings.HNSW_EF_CONSTRUCTION
        )

        # 4. Relatório
        status = IndexManager.verificar_indices(db)
        logger.info("embeddings_completo", indices=status["total"])

    except Exception as e:
        logger.error("erro_embeddings", erro=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
