"""Script de ingestão completa de dados."""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.services.ingestion.cgu_collector import CGUCollector
from app.services.ingestion.camara_collector import CamaraCollector
from app.services.ingestion.normalizer import DataNormalizer
import structlog

logger = structlog.get_logger()


async def ingerir_deputados(normalizer: DataNormalizer, legislaturas: list[int]):
    """Coleta e persiste deputados."""
    collector = CamaraCollector()
    for leg in legislaturas:
        logger.info("coletando_deputados", legislatura=leg)
        deputados = await collector.coletar_deputados(leg)
        for dep in deputados:
            normalizer.upsert_parlamentar(dep)
        normalizer.commit()
        logger.info("deputados_persistidos", legislatura=leg, total=len(deputados))


async def ingerir_emendas(normalizer: DataNormalizer, anos: list[int]):
    """Coleta e persiste emendas."""
    collector = CGUCollector()
    for ano in anos:
        logger.info("coletando_emendas", ano=ano)
        count = 0
        async for emenda_data in collector.coletar_emendas(ano):
            emenda_data = normalizer.vincular_autor(emenda_data)
            normalizer.inserir_emenda(emenda_data)
            count += 1
            if count % 500 == 0:
                normalizer.commit()
                logger.info("emendas_batch", ano=ano, processadas=count)
        normalizer.commit()
        logger.info("emendas_persistidas", ano=ano, total=count)


async def main(anos: list[int], legislaturas: list[int]):
    """Orquestra ingestão completa."""
    logger.info("iniciando_ingestao", anos=anos, legislaturas=legislaturas)

    init_db()
    db = SessionLocal()
    normalizer = DataNormalizer(db)

    try:
        # 1. Deputados primeiro (para vincular autores)
        await ingerir_deputados(normalizer, legislaturas)

        # 2. Emendas
        await ingerir_emendas(normalizer, anos)

        logger.info("ingestao_completa")
    except Exception as e:
        logger.error("erro_ingestao", erro=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de dados")
    parser.add_argument("--anos", default="2020,2021,2022,2023,2024",
                        help="Anos para coletar (separados por vírgula)")
    parser.add_argument("--legislaturas", default="56,57",
                        help="Legislaturas para coletar deputados")
    args = parser.parse_args()

    anos = [int(a.strip()) for a in args.anos.split(",")]
    legislaturas = [int(l.strip()) for l in args.legislaturas.split(",")]

    asyncio.run(main(anos, legislaturas))
