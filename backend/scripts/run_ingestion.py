"""Orquestrador unificado de ingestão com checkpoint e rastreamento de paginação.

Uso:
    python -m scripts.run_ingestion
    python -m scripts.run_ingestion --resume
    python -m scripts.run_ingestion --anos 2024 --legislaturas 57
    python -m scripts.run_ingestion --resume --skip-embeddings
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
import app.models  # noqa: F401 — registra todos os models no Base
from app.services.ingestion.cgu_collector import CGUCollector
from app.services.ingestion.camara_collector import CamaraCollector
from app.services.ingestion.normalizer import DataNormalizer
from app.utils.checkpoint import CheckpointManager, ProgressTracker
import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Etapa 1: Deputados
# ---------------------------------------------------------------------------
async def etapa_deputados(
    normalizer: DataNormalizer,
    legislaturas: list[int],
    checkpoint: CheckpointManager,
):
    """Coleta e persiste deputados por legislatura."""
    collector = CamaraCollector()

    for leg in legislaturas:
        key = str(leg)
        if checkpoint.get_status("deputados", key) == "completed":
            logger.info("deputados_skip", legislatura=leg, motivo="já concluído")
            continue

        checkpoint.mark_started("deputados", key)
        logger.info("coletando_deputados", legislatura=leg)

        deputados = await collector.coletar_deputados(leg)
        for dep in deputados:
            normalizer.upsert_parlamentar(dep)
        normalizer.commit()

        checkpoint.mark_completed("deputados", key, total=len(deputados))
        logger.info("deputados_persistidos", legislatura=leg, total=len(deputados))


# ---------------------------------------------------------------------------
# Etapa 2: Emendas
# ---------------------------------------------------------------------------
async def etapa_emendas(
    normalizer: DataNormalizer,
    anos: list[int],
    checkpoint: CheckpointManager,
):
    """Coleta e persiste emendas por ano com checkpoint por página."""
    collector = CGUCollector()

    for ano in anos:
        key = str(ano)
        if checkpoint.get_status("emendas", key) == "completed":
            logger.info("emendas_skip", ano=ano, motivo="já concluído")
            continue

        start_page = checkpoint.get_last_page("emendas", key) + 1
        checkpoint.mark_started("emendas", key)
        logger.info("coletando_emendas", ano=ano, pagina_inicial=start_page)

        count = 0
        start_time = time.monotonic()

        async for emenda_data in collector.coletar_emendas(ano, start_page=start_page):
            emenda_data = normalizer.vincular_autor(emenda_data)
            normalizer.inserir_emenda(emenda_data)
            count += 1

            if count % 500 == 0:
                normalizer.commit()
                elapsed = time.monotonic() - start_time
                rate = count / elapsed if elapsed > 0 else 0
                logger.info(
                    "emendas_batch",
                    ano=ano,
                    processadas=count,
                    pagina_atual=collector.current_page,
                    taxa_por_seg=round(rate, 2),
                    requests_api=collector.rate_limiter.request_count,
                )
                checkpoint.update_progress(
                    "emendas", key,
                    last_page=collector.current_page,
                    total=count,
                )

        normalizer.commit()
        checkpoint.mark_completed("emendas", key, total=count)
        logger.info("emendas_completas", ano=ano, total=count)


# ---------------------------------------------------------------------------
# Etapa 3: Beneficiários
# ---------------------------------------------------------------------------
async def etapa_beneficiarios(
    checkpoint: CheckpointManager,
    batch_size: int,
):
    """Coleta documentos e beneficiários das emendas."""
    from scripts.ingest_beneficiarios import ingerir_beneficiarios

    key = "global"
    if checkpoint.get_status("beneficiarios", key) == "completed":
        logger.info("beneficiarios_skip", motivo="já concluído")
        return

    start_index = checkpoint.get_value("beneficiarios", key, "last_emenda_index", 0)
    checkpoint.mark_started("beneficiarios", key)
    logger.info("coletando_beneficiarios", retomando_de=start_index)

    def on_batch(i, total_docs, total_benef):
        checkpoint.update_progress(
            "beneficiarios", key,
            last_emenda_index=i,
            total_docs=total_docs,
            total_benef=total_benef,
        )

    result = await ingerir_beneficiarios(
        batch_size=batch_size,
        start_index=start_index,
        on_batch_commit=on_batch,
    )

    if result:
        checkpoint.mark_completed("beneficiarios", key, total=result["emendas"])


# ---------------------------------------------------------------------------
# Etapa 4: Embeddings
# ---------------------------------------------------------------------------
def etapa_embeddings(checkpoint: CheckpointManager):
    """Gera embeddings vetoriais para emendas e classificações."""
    key = "all"
    if checkpoint.get_status("embeddings", key) == "completed":
        logger.info("embeddings_skip", motivo="já concluído")
        return

    checkpoint.mark_started("embeddings", key)
    logger.info("gerando_embeddings")

    from scripts.generate_embeddings import main as generate_main
    generate_main()

    checkpoint.mark_completed("embeddings", key, total=0)


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------
async def main(
    anos: list[int],
    legislaturas: list[int],
    resume: bool = False,
    batch_size: int = 100,
    skip_embeddings: bool = False,
):
    """Orquestra ingestão completa com checkpoint."""
    checkpoint = CheckpointManager()

    if not resume:
        checkpoint.reset()
        logger.info("ingestao_nova", anos=anos, legislaturas=legislaturas)
    else:
        logger.info("retomando_ingestao", checkpoint=checkpoint.summary())

    init_db()
    db = SessionLocal()
    normalizer = DataNormalizer(db)
    start_total = time.monotonic()

    try:
        # 1. Deputados
        logger.info("=== ETAPA 1/4: DEPUTADOS ===")
        await etapa_deputados(normalizer, legislaturas, checkpoint)

        # 2. Emendas
        logger.info("=== ETAPA 2/4: EMENDAS ===")
        await etapa_emendas(normalizer, anos, checkpoint)

        # 3. Beneficiários
        logger.info("=== ETAPA 3/4: BENEFICIÁRIOS ===")
        await etapa_beneficiarios(checkpoint, batch_size)

        # 4. Embeddings
        if not skip_embeddings:
            logger.info("=== ETAPA 4/4: EMBEDDINGS ===")
            etapa_embeddings(checkpoint)
        else:
            logger.info("embeddings_pulado", motivo="--skip-embeddings")

        elapsed_total = time.monotonic() - start_total
        logger.info(
            "ingestao_completa",
            tempo_total_min=round(elapsed_total / 60, 1),
            resumo=checkpoint.summary(),
        )

    except KeyboardInterrupt:
        logger.warning("ingestao_interrompida",
                        resumo=checkpoint.summary(),
                        dica="Execute com --resume para retomar")
        raise
    except Exception as e:
        logger.error("erro_ingestao", erro=str(e), resumo=checkpoint.summary())
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestão completa de dados com rastreamento de paginação"
    )
    parser.add_argument("--anos", default="2020,2021,2022,2023,2024",
                        help="Anos para coletar emendas (separados por vírgula)")
    parser.add_argument("--legislaturas", default="56,57",
                        help="Legislaturas para coletar deputados")
    parser.add_argument("--resume", action="store_true",
                        help="Retomar ingestão do último checkpoint")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Tamanho do batch para commit de beneficiários")
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Pular geração de embeddings")
    args = parser.parse_args()

    anos = [int(a.strip()) for a in args.anos.split(",")]
    legislaturas = [int(l.strip()) for l in args.legislaturas.split(",")]

    asyncio.run(main(
        anos=anos,
        legislaturas=legislaturas,
        resume=args.resume,
        batch_size=args.batch_size,
        skip_embeddings=args.skip_embeddings,
    ))
