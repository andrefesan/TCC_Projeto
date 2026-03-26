"""Backfill de observações nos documentos de emenda via API CGU.

Prioriza documentos vinculados a emendas que as consultas de teste
Type D (beneficiário) atingem diretamente.
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
from app.config import settings
import structlog

logger = structlog.get_logger()

# Filtros derivados das 30 consultas Type D do test_evaluation.py
# Cada tupla: (uf, ano_ou_None)
TYPE_D_FILTERS = [
    ("MG", None), ("DF", 2024), ("RS", None), ("TO", 2023), ("RJ", 2024),
    ("PR", 2023), ("GO", 2024), ("AC", 2024), ("BA", 2023), ("CE", 2024),
    ("RO", 2024), ("MG", 2023), ("RJ", 2024), ("AP", 2023), ("RS", 2024),
    ("PE", 2023), ("PR", 2024), ("AM", 2023), ("AP", 2024), ("MG", 2023),
    ("RJ", 2024), ("SP", 2023), ("RR", 2023), ("RS", 2024), ("SP", 2023),
    ("BA", 2024), ("GO", 2024), ("RJ", 2024), ("PE", 2023), ("MG", None),
]


def _buscar_docs_prioritarios(db, limit: int | None = None) -> list[tuple]:
    """Busca documentos prioritários (Type D) sem observação."""
    # Extrair pares UF+ano únicos
    uf_ano_pairs = set()
    for uf, ano in TYPE_D_FILTERS:
        if ano:
            uf_ano_pairs.add((uf, ano))
        else:
            for y in range(2020, 2025):
                uf_ano_pairs.add((uf, y))

    # Construir WHERE clause dinâmico
    conditions = []
    params = {}
    for i, (uf, ano) in enumerate(sorted(uf_ano_pairs)):
        conditions.append(f"(e.uf = :uf{i} AND e.ano = :ano{i})")
        params[f"uf{i}"] = uf
        params[f"ano{i}"] = ano

    where_clause = " OR ".join(conditions)
    limit_clause = f"LIMIT {limit}" if limit else ""

    result = db.execute(text(f"""
        SELECT d.id, d.codigo_documento
        FROM documentos_emenda d
        JOIN emendas e ON d.emenda_id = e.id
        WHERE d.detalhes_coletados = 1
          AND (d.observacao IS NULL OR d.observacao = '')
          AND ({where_clause})
        ORDER BY e.id
        {limit_clause}
    """), params)
    return [(r.id, r.codigo_documento) for r in result.fetchall()]


def _buscar_docs_restantes(db, limit: int | None = None) -> list[tuple]:
    """Busca todos os documentos restantes sem observação."""
    limit_clause = f"LIMIT {limit}" if limit else ""
    result = db.execute(text(f"""
        SELECT id, codigo_documento
        FROM documentos_emenda
        WHERE detalhes_coletados = 1
          AND (observacao IS NULL OR observacao = '')
        ORDER BY id
        {limit_clause}
    """))
    return [(r.id, r.codigo_documento) for r in result.fetchall()]


async def backfill(docs: list[tuple], db, collector: CGUCollector,
                   batch_size: int = 50):
    """Executa backfill de observações para lista de documentos."""
    total = len(docs)
    atualizados = 0
    erros = 0
    vazios = 0
    t0 = time.monotonic()

    client = await collector.get_shared_client()

    for i in range(0, total, batch_size):
        batch = docs[i:i + batch_size]

        for doc_id, codigo in batch:
            try:
                detalhe = await collector.coletar_detalhes_documento(
                    codigo, client=client
                )
                if detalhe and detalhe.get("observacao"):
                    db.execute(text("""
                        UPDATE documentos_emenda
                        SET observacao = :obs
                        WHERE id = :id
                    """), {"obs": detalhe["observacao"], "id": doc_id})
                    atualizados += 1
                else:
                    vazios += 1
            except Exception as e:
                erros += 1
                if erros <= 5:
                    logger.warning("erro_backfill", codigo=codigo, erro=str(e)[:100])

        db.commit()

        pos = min(i + batch_size, total)
        elapsed = time.monotonic() - t0
        rate = pos / elapsed if elapsed > 0 else 0
        remaining = total - pos
        eta_min = remaining / rate / 60 if rate > 0 else 0

        logger.info("backfill_progresso",
                     pos=pos, total=total,
                     pct=f"{pos/total*100:.1f}%",
                     atualizados=atualizados, vazios=vazios, erros=erros,
                     eta_min=f"{eta_min:.1f}")

    await collector.close_shared_client()
    return atualizados, vazios, erros


async def main():
    parser = argparse.ArgumentParser(
        description="Backfill de observações nos documentos de emenda"
    )
    parser.add_argument("--limit", type=int, default=10000,
                        help="Limite de documentos (default: 10000)")
    parser.add_argument("--todos", action="store_true",
                        help="Processar todos os documentos (sem limite)")
    parser.add_argument("--apenas-restantes", action="store_true",
                        help="Pular prioritários, processar apenas restantes")
    args = parser.parse_args()

    db = SessionLocal()
    collector = CGUCollector()

    try:
        if not args.apenas_restantes:
            # Fase 1: Documentos prioritários (Type D)
            limit_prio = None if args.todos else args.limit
            docs = _buscar_docs_prioritarios(db, limit=limit_prio)
            logger.info("backfill_prioritarios", total=len(docs))

            if docs:
                atualiz, vazios, erros = await backfill(docs, db, collector)
                logger.info("backfill_prioritarios_completo",
                             atualizados=atualiz, vazios=vazios, erros=erros)

        if args.todos or args.apenas_restantes:
            # Fase 2: Restantes
            docs = _buscar_docs_restantes(db)
            logger.info("backfill_restantes", total=len(docs))

            if docs:
                atualiz, vazios, erros = await backfill(docs, db, collector)
                logger.info("backfill_restantes_completo",
                             atualizados=atualiz, vazios=vazios, erros=erros)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
