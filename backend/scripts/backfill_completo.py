"""Backfill completo — busca campos faltantes na API CGU.

Fase 1: Emendas sem valorLiquidado — re-busca /emendas por ano/página
Fase 2: Documentos com valor=0 — re-busca /despesas/documentos/{codigo}
Fase 3: Reconcilia emendas a partir dos documentos

Uso:
    python scripts/backfill_completo.py                   # tudo
    python scripts/backfill_completo.py --fase documentos  # só docs
    python scripts/backfill_completo.py --fase emendas     # só emendas
    python scripts/backfill_completo.py --uf SC            # filtrar UF
    python scripts/backfill_completo.py --resume           # retomar
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

CHECKPOINT_DIR = Path(__file__).parent.parent / "data"


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
    """Concorrência fixa — 6 chaves × 400 RPM = 2400 RPM = 40 req/s.
    Usa 8 conexões simultâneas para manter ~30-35 req/s efetivos."""
    return 8


# ─── FASE 1: Re-fetch emendas para preencher valorLiquidado + restos ────────

async def fase_emendas():
    """Re-busca emendas na API para preencher campos faltantes."""
    init_db()
    db = SessionLocal()
    collector = CGUCollector()

    try:
        # Quais emendas precisam de update
        result = db.execute(text("""
            SELECT COUNT(*) FROM emendas
            WHERE valor_liquidado = 0 OR valor_liquidado IS NULL
        """))
        total_sem = result.scalar()
        logger.info("emendas_sem_liquidado", total=total_sem)

        atualizadas = 0
        for ano in range(2020, 2025):
            pagina = 1
            logger.info("buscando_emendas_api", ano=ano)

            while True:
                headers = await collector._acquire_and_get_headers()
                try:
                    client = await collector.get_shared_client()
                    response = await client.get(
                        f"{collector.BASE_URL}/emendas",
                        params={"ano": ano, "pagina": pagina},
                        headers=headers,
                    )

                    if response.status_code in (429, 401, 405):
                        await asyncio.sleep(5)
                        continue
                    if response.status_code == 404:
                        break

                    response.raise_for_status()
                    data = response.json()
                    if not data:
                        break

                    for raw in data:
                        codigo = raw.get("codigoEmenda", "")
                        if not codigo:
                            continue

                        val_liq = _parse_valor(raw.get("valorLiquidado", "0"))
                        val_emp = _parse_valor(raw.get("valorEmpenhado", "0"))
                        val_pag = _parse_valor(raw.get("valorPago", "0"))
                        val_ri = _parse_valor(raw.get("valorRestoInscrito", "0"))
                        val_rc = _parse_valor(raw.get("valorRestoCancelado", "0"))
                        val_rp = _parse_valor(raw.get("valorRestoPago", "0"))
                        num = raw.get("numeroEmenda", "")

                        db.execute(text("""
                            UPDATE emendas SET
                                valor_liquidado = CASE WHEN :val_liq > valor_liquidado
                                    THEN :val_liq ELSE valor_liquidado END,
                                valor_empenhado = CASE WHEN :val_emp > valor_empenhado
                                    THEN :val_emp ELSE valor_empenhado END,
                                valor_pago = CASE WHEN :val_pag > valor_pago
                                    THEN :val_pag ELSE valor_pago END,
                                valor_resto_inscrito = :val_ri,
                                valor_resto_cancelado = :val_rc,
                                valor_resto_pago = :val_rp,
                                numero_emenda = COALESCE(NULLIF(:num, ''), numero_emenda)
                            WHERE codigo_emenda = :codigo
                        """), {
                            "val_liq": val_liq, "val_emp": val_emp, "val_pag": val_pag,
                            "val_ri": val_ri, "val_rc": val_rc, "val_rp": val_rp,
                            "num": num, "codigo": codigo,
                        })
                        atualizadas += 1

                    if pagina % 5 == 0:
                        db.commit()
                        logger.info("emendas_progresso", ano=ano, pagina=pagina,
                                    atualizadas=atualizadas)

                    pagina += 1

                except Exception as e:
                    logger.warning("erro_emendas", ano=ano, pagina=pagina, erro=str(e)[:100])
                    await asyncio.sleep(5)
                    continue

            db.commit()
            logger.info("emendas_ano_completo", ano=ano, atualizadas=atualizadas)

        # Verificação
        result = db.execute(text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN valor_liquidado > 0 THEN 1 ELSE 0 END) as com_liq
            FROM emendas
        """))
        row = result.fetchone()
        logger.info("emendas_backfill_completo", total=row[0], com_liquidado=row[1],
                     atualizadas_total=atualizadas)

    finally:
        await collector.close_shared_client()
        db.close()


# ─── FASE 2: Re-fetch documentos para valor ─────────────────────────────────

async def fase_documentos(uf_filter: str | None = None, resume: bool = False):
    """Re-busca valor de cada documento no endpoint de detalhes."""
    init_db()
    db = SessionLocal()
    collector = CGUCollector()
    checkpoint_file = CHECKPOINT_DIR / "checkpoint_backfill_docs.txt"

    try:
        query = """
            SELECT d.id, d.codigo_documento
            FROM documentos_emenda d
            JOIN emendas e ON d.emenda_id = e.id
            WHERE (d.valor IS NULL OR d.valor = 0)
        """
        params = {}
        if uf_filter:
            query += " AND e.uf = :uf"
            params["uf"] = uf_filter.upper()
        query += " ORDER BY d.id"

        result = db.execute(text(query), params)
        documentos = [(r.id, r.codigo_documento) for r in result.fetchall()]

        last_id = 0
        if resume and checkpoint_file.exists():
            last_id = int(checkpoint_file.read_text().strip())
            documentos = [(did, cod) for did, cod in documentos if did > last_id]

        total = len(documentos)
        logger.info("docs_backfill_inicio", total=total, uf=uf_filter or "todas")
        if total == 0:
            return

        n_concurrent = _get_concurrency()
        semaphore = asyncio.Semaphore(n_concurrent)
        atualizados = 0
        erros = 0
        zeros = 0
        t0 = time.monotonic()

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
                    doc_id, codigo = documentos[idx]
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
                    checkpoint_file.write_text(str(doc_id))

                processed = atualizados + erros + zeros
                if processed % 1000 == 0 and processed > 0:
                    elapsed = time.monotonic() - t0
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = total - processed
                    eta_min = remaining / rate / 60 if rate > 0 else 0
                    logger.info("docs_progresso",
                                processed=f"{processed:,}", total=f"{total:,}",
                                pct=f"{processed/total*100:.1f}%",
                                atualizados=atualizados, erros=erros,
                                rate=f"{rate:.1f}/s",
                                eta_min=f"{eta_min:.0f}")

        await asyncio.gather(producer(), consumer())

        elapsed = time.monotonic() - t0
        logger.info("docs_backfill_completo",
                     atualizados=atualizados, erros=erros, zeros=zeros,
                     elapsed_min=f"{elapsed/60:.1f}")

        if checkpoint_file.exists():
            checkpoint_file.unlink()

    finally:
        await collector.close_shared_client()
        db.close()


# ─── FASE 3: Reconciliação ──────────────────────────────────────────────────

def fase_reconciliacao():
    """Recalcula valores das emendas a partir dos documentos."""
    init_db()
    db = SessionLocal()
    try:
        from app.services.ingestion.normalizer import DataNormalizer
        normalizer = DataNormalizer(db)
        is_sqlite = "sqlite" in str(db.bind.url)
        if is_sqlite:
            normalizer.recalcular_valores_de_documentos_sqlite()
        else:
            normalizer.recalcular_valores_de_documentos()
        logger.info("reconciliacao_completa")
    finally:
        db.close()


# ─── Main ────────────────────────────────────────────────────────────────────

async def main(fase: str | None, uf: str | None, resume: bool):
    fases = ["emendas", "documentos", "reconciliacao"] if not fase else [fase]

    for f in fases:
        logger.info(f"{'='*50}")
        logger.info(f"FASE: {f.upper()}")
        logger.info(f"{'='*50}")

        if f == "emendas":
            await fase_emendas()
        elif f == "documentos":
            await fase_documentos(uf_filter=uf, resume=resume)
        elif f == "reconciliacao":
            fase_reconciliacao()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill completo")
    parser.add_argument("--fase", choices=["emendas", "documentos", "reconciliacao"])
    parser.add_argument("--uf", type=str, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    asyncio.run(main(fase=args.fase, uf=args.uf, resume=args.resume))
