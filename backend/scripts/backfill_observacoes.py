"""Backfill de observações nos documentos de emenda via API CGU.

Estratégia em duas camadas:
  1. Tenta /despesas/documentos/{codigo_documento} (endpoint de detalhes)
  2. Se vazio, tenta /emendas/documentos/{codigo_emenda} (endpoint Phase 2)
     e localiza o documento pelo codigo_documento na lista retornada.
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal
from app.services.ingestion.cgu_collector import CGUCollector
import structlog

logger = structlog.get_logger()


def _buscar_docs_sem_observacao(db, limit: int | None = None) -> list[tuple]:
    """Busca documentos com detalhes coletados mas sem observação.

    Retorna (doc_id, codigo_documento, codigo_emenda) para permitir
    fallback via endpoint Phase 2.
    """
    limit_clause = f"LIMIT {limit}" if limit else ""
    result = db.execute(text(f"""
        SELECT d.id, d.codigo_documento, e.codigo_emenda
        FROM documentos_emenda d
        JOIN emendas e ON d.emenda_id = e.id
        WHERE d.detalhes_coletados = 1
          AND (d.observacao IS NULL OR d.observacao = '')
        ORDER BY e.id
        {limit_clause}
    """))
    return [(r.id, r.codigo_documento, r.codigo_emenda) for r in result.fetchall()]


async def backfill(docs: list[tuple], db, collector: CGUCollector,
                   batch_size: int = 50, concurrency: int = 10):
    """Executa backfill de observações com fallback Phase 2."""
    total = len(docs)
    atualizados = 0
    erros = 0
    vazios = 0
    fallback_hits = 0
    t0 = time.monotonic()

    client = await collector.get_shared_client()
    semaphore = asyncio.Semaphore(concurrency)

    # Cache de respostas Phase 2 para evitar re-fetch da mesma emenda
    cache_phase2: dict[str, dict[str, str]] = {}  # codigo_emenda -> {codigo_doc: obs}

    async def fetch_obs_phase1(codigo_doc: str) -> str | None:
        """Tenta obter observação via /despesas/documentos/{codigo}."""
        async with semaphore:
            detalhe = await collector.coletar_detalhes_documento(
                codigo_doc, client=client
            )
            if detalhe and detalhe.get("observacao"):
                return detalhe["observacao"]
            return None

    async def fetch_obs_phase2(codigo_emenda: str, codigo_doc: str) -> str | None:
        """Tenta obter observação via /emendas/documentos/{codigo_emenda}."""
        if codigo_emenda not in cache_phase2:
            try:
                docs_emenda = await collector.coletar_documentos_emenda(codigo_emenda)
                cache_phase2[codigo_emenda] = {
                    d["codigo_documento"]: d.get("observacao", "")
                    for d in docs_emenda
                }
            except Exception:
                cache_phase2[codigo_emenda] = {}

        return cache_phase2[codigo_emenda].get(codigo_doc) or None

    for i in range(0, total, batch_size):
        batch = docs[i:i + batch_size]

        for doc_id, codigo_doc, codigo_emenda in batch:
            try:
                # Camada 1: endpoint de detalhes
                obs = await fetch_obs_phase1(codigo_doc)

                # Camada 2: fallback via endpoint Phase 2
                if not obs:
                    obs = await fetch_obs_phase2(codigo_emenda, codigo_doc)
                    if obs:
                        fallback_hits += 1

                if obs:
                    db.execute(text("""
                        UPDATE documentos_emenda
                        SET observacao = :obs
                        WHERE id = :id
                    """), {"obs": obs, "id": doc_id})
                    atualizados += 1
                else:
                    vazios += 1
            except Exception as e:
                erros += 1
                if erros <= 10:
                    logger.warning("erro_backfill", codigo=codigo_doc, erro=str(e)[:100])

        db.commit()

        pos = min(i + batch_size, total)
        elapsed = time.monotonic() - t0
        rate = pos / elapsed if elapsed > 0 else 0
        remaining = total - pos
        eta_min = remaining / rate / 60 if rate > 0 else 0

        logger.info("backfill_progresso",
                     pos=pos, total=total,
                     pct=f"{pos/total*100:.1f}%",
                     atualizados=atualizados, fallback=fallback_hits,
                     vazios=vazios, erros=erros,
                     eta_min=f"{eta_min:.1f}")

    await collector.close_shared_client()
    return atualizados, fallback_hits, vazios, erros


async def main():
    parser = argparse.ArgumentParser(
        description="Backfill de observações nos documentos de emenda"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Limite de documentos (default: todos)")
    parser.add_argument("--batch", type=int, default=50,
                        help="Tamanho do batch para commit (default: 50)")
    parser.add_argument("--concurrency", type=int, default=10,
                        help="Concorrência de requests (default: 10)")
    args = parser.parse_args()

    db = SessionLocal()
    collector = CGUCollector()

    try:
        docs = _buscar_docs_sem_observacao(db, limit=args.limit)
        logger.info("backfill_inicio", total=len(docs))

        if docs:
            atualiz, fallback, vazios, erros = await backfill(
                docs, db, collector,
                batch_size=args.batch,
                concurrency=args.concurrency,
            )
            logger.info("backfill_completo",
                         atualizados=atualiz, fallback_phase2=fallback,
                         vazios=vazios, erros=erros)
        else:
            logger.info("nada_para_backfill")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
