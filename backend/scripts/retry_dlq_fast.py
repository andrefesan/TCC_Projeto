"""Retry concorrente da Dead Letter Queue (detalhes).

Busca detalhes dos documentos da DLQ, atualiza o banco, e limpa a DLQ ao final.
"""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db
from app.services.ingestion.cgu_collector import CGUCollector
from scripts.run_ingestion_brasil import (
    _atualizar_documento_detalhes,
    _popular_lookups_detalhe,
    _popular_favorecido,
)
import structlog

logger = structlog.get_logger()

DLQ_PATH = Path(__file__).parent.parent / "data" / "dead_letter_brasil.json"


async def main():
    init_db()
    db = SessionLocal()
    if hasattr(db, 'execute'):
        db.execute(text("PRAGMA synchronous=FULL"))

    # Carregar DLQ
    dlq_items = json.loads(DLQ_PATH.read_text(encoding="utf-8"))
    codigos = [item["identificador"] for item in dlq_items if item["fase"] == "detalhes"]
    total = len(codigos)
    logger.info("dlq_retry_inicio", total=total)

    if not total:
        return

    # Mapear codigo_documento -> doc_id no banco
    doc_map = {}
    for i in range(0, len(codigos), 500):
        batch_codes = codigos[i:i+500]
        placeholders = ",".join(f":c{j}" for j in range(len(batch_codes)))
        params = {f"c{j}": c for j, c in enumerate(batch_codes)}
        rows = db.execute(text(
            f"SELECT id, codigo_documento FROM documentos_emenda "
            f"WHERE codigo_documento IN ({placeholders})"
        ), params).fetchall()
        for r in rows:
            doc_map[r.codigo_documento] = r.id

    logger.info("docs_encontrados_no_banco", encontrados=len(doc_map), total_dlq=total)

    collector = CGUCollector()
    client = await collector.get_shared_client()
    semaphore = asyncio.Semaphore(40)

    resolvidos = 0
    erros = 0
    vazios = 0
    t0 = time.monotonic()
    resolved_codes = set()

    async def fetch(codigo):
        async with semaphore:
            try:
                detalhe = await collector.coletar_detalhes_documento(
                    codigo, client=client
                )
                return codigo, detalhe, None
            except Exception as e:
                return codigo, None, str(e)[:200]

    # Processar em batches de 200
    commit_every = 1000
    uncommitted = 0

    for i in range(0, total, 200):
        batch = codigos[i:i+200]
        tasks = [fetch(c) for c in batch]
        results = await asyncio.gather(*tasks)

        for codigo, detalhe, error in results:
            doc_id = doc_map.get(codigo)
            if not doc_id:
                resolved_codes.add(codigo)  # não existe no banco, remover da DLQ
                continue

            if error:
                erros += 1
                if erros <= 10:
                    logger.warning("dlq_erro", codigo=codigo, erro=error[:80])
            elif detalhe:
                _atualizar_documento_detalhes(db, doc_id, detalhe)
                _popular_lookups_detalhe(db, detalhe)
                _popular_favorecido(db, doc_id, detalhe)
                resolvidos += 1
                uncommitted += 1
                resolved_codes.add(codigo)
            else:
                # 404 — marcar como coletado
                db.execute(text(
                    "UPDATE documentos_emenda SET detalhes_coletados = 1 WHERE id = :id"
                ), {"id": doc_id})
                vazios += 1
                uncommitted += 1
                resolved_codes.add(codigo)

            if uncommitted >= commit_every:
                db.commit()
                uncommitted = 0

        if uncommitted:
            db.commit()
            uncommitted = 0

        pos = min(i + 200, total)
        elapsed = time.monotonic() - t0
        rate = pos / elapsed if elapsed > 0 else 0
        eta_min = (total - pos) / rate / 60 if rate > 0 else 0
        logger.info("dlq_progresso", pos=pos, total=total,
                    pct=f"{pos/total*100:.1f}%",
                    resolvidos=resolvidos, vazios=vazios, erros=erros,
                    eta_min=f"{eta_min:.1f}")

    # Limpar DLQ — remover resolvidos
    remaining = [item for item in dlq_items
                 if not (item["fase"] == "detalhes" and item["identificador"] in resolved_codes)]
    DLQ_PATH.write_text(
        json.dumps(remaining, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    await collector.close_shared_client()
    db.close()
    logger.info("dlq_retry_completo", resolvidos=resolvidos, vazios=vazios,
                erros=erros, restante_dlq=len(remaining))


if __name__ == "__main__":
    asyncio.run(main())
