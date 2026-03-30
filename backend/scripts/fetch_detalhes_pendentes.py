"""Busca detalhes de documentos pendentes + backfill de observações.

Duas fases:
  1. Docs sem detalhes_coletados — fetch completo de detalhes
  2. Docs com detalhes mas sem observação — re-fetch com fallback Phase 2

Com rate limiter por chave (7 chaves x 400 RPM = 2800 RPM).

Mitigações de durabilidade:
  - Commit individual por documento (não por batch)
  - PRAGMA synchronous=FULL para garantir fsync antes de confirmar
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db, engine, is_sqlite
from app.services.ingestion.cgu_collector import CGUCollector
from scripts.run_ingestion_brasil import (
    _atualizar_documento_detalhes,
    _popular_lookups_detalhe,
    _popular_favorecido,
)
import structlog

logger = structlog.get_logger()


def _safe_session():
    """Cria sessão com synchronous=FULL para durabilidade máxima."""
    db = SessionLocal()
    if is_sqlite():
        db.execute(text("PRAGMA synchronous=FULL"))
    return db


# ---------------------------------------------------------------------------
# Fase 1: Docs sem detalhes coletados
# ---------------------------------------------------------------------------
async def fase1_detalhes_pendentes(db, collector: CGUCollector, concurrency: int):
    """Busca detalhes de documentos que nunca foram coletados."""
    result = db.execute(text("""
        SELECT d.id, d.codigo_documento
        FROM documentos_emenda d
        WHERE d.detalhes_coletados IS NULL OR d.detalhes_coletados = 0
        ORDER BY d.id
    """))
    docs = [(r.id, r.codigo_documento) for r in result.fetchall()]
    total = len(docs)
    logger.info("fase1_inicio", total=total)

    if not total:
        return

    client = await collector.get_shared_client()
    coletados = 0
    erros = 0
    vazios = 0
    t0 = time.monotonic()
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_one(doc_id, codigo):
        async with semaphore:
            try:
                detalhe = await collector.coletar_detalhes_documento(
                    codigo, client=client
                )
                return doc_id, codigo, detalhe, None
            except Exception as e:
                return doc_id, codigo, None, str(e)[:200]

    # Fetch em batches de 200 (concorrência), commit a cada 20 docs (durabilidade)
    fetch_size = 200
    commit_every = 1000
    uncommitted = 0

    for i in range(0, total, fetch_size):
        batch = docs[i:i + fetch_size]
        tasks = [fetch_one(doc_id, codigo) for doc_id, codigo in batch]
        results = await asyncio.gather(*tasks)

        for doc_id, codigo, detalhe, error in results:
            if error:
                erros += 1
                if erros <= 10:
                    logger.warning("erro_detalhe", codigo=codigo, erro=error[:80])
            elif detalhe:
                _atualizar_documento_detalhes(db, doc_id, detalhe)
                _popular_lookups_detalhe(db, detalhe)
                _popular_favorecido(db, doc_id, detalhe)
                coletados += 1
                uncommitted += 1
            else:
                db.execute(text(
                    "UPDATE documentos_emenda SET detalhes_coletados = 1 "
                    "WHERE id = :id"
                ), {"id": doc_id})
                vazios += 1
                uncommitted += 1

            if uncommitted >= commit_every:
                db.commit()
                uncommitted = 0

        if uncommitted:
            db.commit()
            uncommitted = 0

        pos = min(i + fetch_size, total)
        elapsed = time.monotonic() - t0
        rate = pos / elapsed if elapsed > 0 else 0
        eta_min = (total - pos) / rate / 60 if rate > 0 else 0
        logger.info("fase1_progresso", pos=pos, total=total,
                    pct=f"{pos/total*100:.1f}%",
                    coletados=coletados, vazios=vazios, erros=erros,
                    eta_min=f"{eta_min:.1f}")

    logger.info("fase1_completa", coletados=coletados, vazios=vazios, erros=erros)


# ---------------------------------------------------------------------------
# Fase 2: Backfill de observações
# ---------------------------------------------------------------------------
async def fase2_backfill_observacoes(db, collector: CGUCollector,
                                      concurrency: int, limit: int | None = None):
    """Re-fetch observações de docs que ficaram com observacao vazia."""
    limit_clause = f"LIMIT {limit}" if limit else ""
    result = db.execute(text(f"""
        SELECT d.id, d.codigo_documento, e.codigo_emenda
        FROM documentos_emenda d
        JOIN emendas e ON d.emenda_id = e.id
        WHERE d.detalhes_coletados = 1
          AND (d.observacao IS NULL OR d.observacao = '')
        ORDER BY d.id
        {limit_clause}
    """))
    docs = [(r.id, r.codigo_documento, r.codigo_emenda) for r in result.fetchall()]
    total = len(docs)
    logger.info("fase2_inicio", total=total)

    if not total:
        return

    client = await collector.get_shared_client()
    atualizados = 0
    erros = 0
    vazios = 0
    fallback_hits = 0
    t0 = time.monotonic()
    semaphore = asyncio.Semaphore(concurrency)

    # Cache Phase 2 por emenda
    cache_phase2: dict[str, dict[str, str]] = {}

    async def fetch_obs(doc_id, codigo_doc, codigo_emenda):
        async with semaphore:
            try:
                # Camada 1: endpoint detalhes
                detalhe = await collector.coletar_detalhes_documento(
                    codigo_doc, client=client
                )
                if detalhe and detalhe.get("observacao"):
                    return doc_id, detalhe["observacao"], False, None

                # Camada 2: fallback Phase 2
                if codigo_emenda not in cache_phase2:
                    try:
                        docs_emenda = await collector.coletar_documentos_emenda(codigo_emenda)
                        cache_phase2[codigo_emenda] = {
                            d["codigo_documento"]: d.get("observacao", "")
                            for d in docs_emenda
                        }
                    except Exception:
                        cache_phase2[codigo_emenda] = {}

                obs_p2 = cache_phase2.get(codigo_emenda, {}).get(codigo_doc)
                if obs_p2:
                    return doc_id, obs_p2, True, None

                return doc_id, None, False, None
            except Exception as e:
                return doc_id, None, False, str(e)[:200]

    # Fetch em batches de 200, commit a cada 20 docs
    fetch_size = 200
    commit_every = 1000
    uncommitted = 0

    for i in range(0, total, fetch_size):
        batch = docs[i:i + fetch_size]
        tasks = [fetch_obs(did, cdoc, cemenda) for did, cdoc, cemenda in batch]
        results = await asyncio.gather(*tasks)

        for doc_id, obs, is_fallback, error in results:
            if error:
                erros += 1
                if erros <= 10:
                    logger.warning("erro_backfill", doc_id=doc_id, erro=error[:80])
            elif obs:
                db.execute(text(
                    "UPDATE documentos_emenda SET observacao = :obs WHERE id = :id"
                ), {"obs": obs, "id": doc_id})
                atualizados += 1
                uncommitted += 1
                if is_fallback:
                    fallback_hits += 1
            else:
                vazios += 1

            if uncommitted >= commit_every:
                db.commit()
                uncommitted = 0

        if uncommitted:
            db.commit()
            uncommitted = 0

        pos = min(i + fetch_size, total)
        elapsed = time.monotonic() - t0
        rate = pos / elapsed if elapsed > 0 else 0
        eta_min = (total - pos) / rate / 60 if rate > 0 else 0
        logger.info("fase2_progresso", pos=pos, total=total,
                    pct=f"{pos/total*100:.1f}%",
                    atualizados=atualizados, fallback=fallback_hits,
                    vazios=vazios, erros=erros,
                    eta_min=f"{eta_min:.1f}")

    logger.info("fase2_completa", atualizados=atualizados,
                fallback_phase2=fallback_hits, vazios=vazios, erros=erros)


async def main():
    parser = argparse.ArgumentParser(
        description="Fetch detalhes pendentes + backfill observações"
    )
    parser.add_argument("--fase", choices=["1", "2", "todas"], default="todas",
                        help="Fase a executar (1=detalhes, 2=backfill, todas)")
    parser.add_argument("--concurrency", type=int, default=20,
                        help="Concorrência de requests (default: 20)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limite de docs na fase 2 (default: todos)")
    args = parser.parse_args()

    init_db()
    db = _safe_session()
    collector = CGUCollector()
    logger.info("durabilidade", synchronous="FULL", commit_every=20)

    try:
        if args.fase in ("1", "todas"):
            await fase1_detalhes_pendentes(db, collector, args.concurrency)

        if args.fase in ("2", "todas"):
            await fase2_backfill_observacoes(db, collector, args.concurrency,
                                              limit=args.limit)
    finally:
        await collector.close_shared_client()
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
