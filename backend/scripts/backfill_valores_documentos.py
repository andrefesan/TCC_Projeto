"""Backfill de valores dos documentos de emenda.

O endpoint /emendas/documentos/{codigo} NÃO retorna o campo 'valor'.
O endpoint /despesas/documentos/{codigo} retorna 'valor' no formato BR.
Este script re-busca o valor de cada documento e atualiza o banco local.

Uso:
    python scripts/backfill_valores_documentos.py
    python scripts/backfill_valores_documentos.py --limit 1000   # testar com poucos
    python scripts/backfill_valores_documentos.py --uf SC        # apenas uma UF
    python scripts/backfill_valores_documentos.py --resume       # retomar
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

from sqlalchemy import text
from app.database import SessionLocal, init_db
from app.services.ingestion.cgu_collector import CGUCollector
import structlog

logger = structlog.get_logger()

CHECKPOINT_FILE = Path(__file__).parent.parent / "data" / "checkpoint_backfill_valores.txt"


def _parse_valor(valor_str) -> float:
    if not valor_str:
        return 0.0
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    cleaned = str(valor_str).strip()
    if cleaned in ("-", "", "N/A", "null"):
        return 0.0
    try:
        return float(cleaned.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def _get_concurrency():
    hour = datetime.now().hour
    if 0 <= hour < 6:
        return 20
    elif 6 <= hour < 8 or 22 <= hour < 24:
        return 15
    else:
        return 10


async def backfill(limit: int | None = None, uf_filter: str | None = None,
                   resume: bool = False):
    init_db()
    db = SessionLocal()
    collector = CGUCollector()

    try:
        # Buscar documentos com valor = 0 (ou NULL)
        query = """
            SELECT d.id, d.codigo_documento, e.uf
            FROM documentos_emenda d
            JOIN emendas e ON d.emenda_id = e.id
            WHERE (d.valor IS NULL OR d.valor = 0)
        """
        params = {}
        if uf_filter:
            query += " AND e.uf = :uf"
            params["uf"] = uf_filter.upper()
        query += " ORDER BY d.id"
        if limit:
            query += f" LIMIT {int(limit)}"

        result = db.execute(text(query), params)
        documentos = [(r.id, r.codigo_documento, r.uf) for r in result.fetchall()]

        # Resume: skip already processed
        last_id = 0
        if resume and CHECKPOINT_FILE.exists():
            last_id = int(CHECKPOINT_FILE.read_text().strip())
            documentos = [(did, cod, uf) for did, cod, uf in documentos if did > last_id]
            logger.info("resuming", last_id=last_id, remaining=len(documentos))

        total = len(documentos)
        logger.info("backfill_inicio", total=total, uf=uf_filter or "todas")

        if total == 0:
            logger.info("nenhum_documento_para_backfill")
            return

        n_concurrent = _get_concurrency()
        semaphore = asyncio.Semaphore(n_concurrent)
        atualizados = 0
        erros = 0
        zeros = 0
        t0 = time.monotonic()

        # Pipeline: producer/consumer com queue
        queue: asyncio.Queue = asyncio.Queue(maxsize=n_concurrent * 4)

        async def fetch_one(doc_id, codigo):
            async with semaphore:
                for tentativa in range(1, 4):
                    try:
                        detalhe = await collector.coletar_detalhes_documento(codigo)
                        return doc_id, codigo, detalhe, None
                    except Exception as e:
                        if tentativa < 3:
                            await asyncio.sleep(tentativa * 3)
                        else:
                            return doc_id, codigo, None, str(e)[:120]

        async def producer():
            tasks = set()
            idx = 0
            while idx < len(documentos) or tasks:
                while idx < len(documentos) and len(tasks) < n_concurrent:
                    doc_id, codigo, uf = documentos[idx]
                    task = asyncio.create_task(fetch_one(doc_id, codigo))
                    task._idx = idx
                    tasks.add(task)
                    idx += 1

                if not tasks:
                    break

                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    await queue.put(task.result())

            await queue.put(None)

        async def consumer():
            nonlocal atualizados, erros, zeros
            commit_count = 0

            while True:
                item = await queue.get()
                if item is None:
                    if commit_count > 0:
                        db.commit()
                    break

                doc_id, codigo, detalhe, error = item

                if error:
                    erros += 1
                elif detalhe:
                    valor = _parse_valor(detalhe.get("valor", "0"))
                    if valor > 0:
                        db.execute(text(
                            "UPDATE documentos_emenda SET valor = :valor WHERE id = :id"
                        ), {"valor": valor, "id": doc_id})
                        atualizados += 1
                    else:
                        zeros += 1
                else:
                    zeros += 1

                commit_count += 1
                if commit_count >= 100:
                    db.commit()
                    commit_count = 0
                    # Save checkpoint
                    CHECKPOINT_FILE.write_text(str(doc_id))

                processed = atualizados + erros + zeros
                if processed % 500 == 0:
                    elapsed = time.monotonic() - t0
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = total - processed
                    eta_min = remaining / rate / 60 if rate > 0 else 0
                    pct = processed / total * 100
                    logger.info("progresso_backfill",
                                processed=processed, total=total,
                                pct=f"{pct:.1f}%",
                                atualizados=atualizados, erros=erros,
                                zeros=zeros, rate=f"{rate:.1f}/s",
                                eta_min=f"{eta_min:.1f}")

        await asyncio.gather(producer(), consumer())

        elapsed = time.monotonic() - t0
        logger.info("backfill_completo",
                     atualizados=atualizados, erros=erros, zeros=zeros,
                     elapsed_min=f"{elapsed/60:.1f}")

        # Reconciliar valores das emendas
        if atualizados > 0:
            logger.info("reconciliando_valores_emendas")
            from app.services.ingestion.normalizer import DataNormalizer
            normalizer = DataNormalizer(db)
            is_sqlite = "sqlite" in str(db.bind.url)
            if is_sqlite:
                normalizer.recalcular_valores_de_documentos_sqlite()
            else:
                normalizer.recalcular_valores_de_documentos()
            logger.info("reconciliacao_completa")

        # Cleanup checkpoint
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

    finally:
        await collector.close_shared_client()
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill valores documentos")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--uf", type=str, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    asyncio.run(backfill(limit=args.limit, uf_filter=args.uf, resume=args.resume))
