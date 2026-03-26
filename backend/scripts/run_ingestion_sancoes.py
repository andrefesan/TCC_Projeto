"""Ingestão de cadastros de sanções (CEIS, CNEP, CEPIM, CEAF) e convênios.

Uso:
    python scripts/run_ingestion_sancoes.py
    python scripts/run_ingestion_sancoes.py --resume
    python scripts/run_ingestion_sancoes.py --tipo ceis
    python scripts/run_ingestion_sancoes.py --tipo convenios --ano 2023
"""
import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db, engine
import app.models  # noqa: F401
from app.services.ingestion.cgu_collector import CGUCollector
from app.utils.checkpoint import CheckpointManager
import structlog

logger = structlog.get_logger()

CHECKPOINT_PATH = Path(__file__).parent.parent / "data" / "checkpoint_sancoes.json"
ANOS_CONVENIOS = [2020, 2021, 2022, 2023, 2024]


def _parse_date(date_str):
    if not date_str:
        return None
    if not isinstance(date_str, str):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _safe_str(val):
    """Garante que o valor seja string ou None (nunca dict/list)."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        for k in ("descricao", "nome", "razaoSocial", "sigla"):
            if k in val and isinstance(val[k], str):
                return val[k].strip()
        return str(val)
    return str(val)


def stats():
    with engine.connect() as c:
        for t in ["sancoes_ceis", "sancoes_cnep", "sancoes_cepim", "sancoes_ceaf",
                   "convenios"]:
            try:
                count = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                logger.info(f"  {t}: {count:,}")
            except Exception:
                logger.info(f"  {t}: (tabela não existe)")


# ---------------------------------------------------------------------------
# Sanções
# ---------------------------------------------------------------------------
async def coletar_ceis(cp: CheckpointManager):
    if cp.get_status("sancoes", "ceis") == "completed":
        logger.info("ceis_skip")
        return

    start_page = cp.get_last_page("sancoes", "ceis") + 1
    cp.mark_started("sancoes", "ceis")
    collector = CGUCollector()
    init_db()
    db = SessionLocal()
    count = 0

    try:
        # Limpar dados anteriores para refresh completo
        if start_page == 1:
            db.execute(text("DELETE FROM sancoes_ceis"))
            db.commit()

        async for item in collector.coletar_sancoes_ceis(start_page):
            db.execute(text("""
                INSERT INTO sancoes_ceis (cpf_cnpj, nome, tipo_sancao,
                    orgao_sancionador, data_inicio, data_fim, fundamentacao)
                VALUES (:cpf, :nome, :tipo, :orgao, :di, :df, :fund)
            """), {
                "cpf": item["cpf_cnpj"], "nome": item["nome"],
                "tipo": item["tipo_sancao"], "orgao": item["orgao_sancionador"],
                "di": _parse_date(item.get("data_inicio")),
                "df": _parse_date(item.get("data_fim")),
                "fund": item.get("fundamentacao", ""),
            })
            count += 1
            if count % 100 == 0:
                db.commit()
                cp.update_progress("sancoes", "ceis",
                                   last_page=collector.current_page, total=count)
                logger.info("ceis_progresso", count=count)

        db.commit()
    finally:
        db.close()

    cp.mark_completed("sancoes", "ceis", total=count)
    logger.info("ceis_completo", total=count)


async def coletar_cnep(cp: CheckpointManager):
    if cp.get_status("sancoes", "cnep") == "completed":
        logger.info("cnep_skip")
        return

    start_page = cp.get_last_page("sancoes", "cnep") + 1
    cp.mark_started("sancoes", "cnep")
    collector = CGUCollector()
    init_db()
    db = SessionLocal()
    count = 0

    try:
        if start_page == 1:
            db.execute(text("DELETE FROM sancoes_cnep"))
            db.commit()

        async for item in collector.coletar_sancoes_cnep(start_page):
            db.execute(text("""
                INSERT INTO sancoes_cnep (cpf_cnpj, nome, tipo_sancao,
                    orgao_sancionador, data_inicio, data_fim, valor_multa)
                VALUES (:cpf, :nome, :tipo, :orgao, :di, :df, :multa)
            """), {
                "cpf": item["cpf_cnpj"], "nome": item["nome"],
                "tipo": item["tipo_sancao"], "orgao": item["orgao_sancionador"],
                "di": _parse_date(item.get("data_inicio")),
                "df": _parse_date(item.get("data_fim")),
                "multa": item.get("valor_multa", 0),
            })
            count += 1
            if count % 100 == 0:
                db.commit()
                cp.update_progress("sancoes", "cnep",
                                   last_page=collector.current_page, total=count)
                logger.info("cnep_progresso", count=count)

        db.commit()
    finally:
        db.close()

    cp.mark_completed("sancoes", "cnep", total=count)
    logger.info("cnep_completo", total=count)


async def coletar_cepim(cp: CheckpointManager):
    if cp.get_status("sancoes", "cepim") == "completed":
        logger.info("cepim_skip")
        return

    start_page = cp.get_last_page("sancoes", "cepim") + 1
    cp.mark_started("sancoes", "cepim")
    collector = CGUCollector()
    init_db()
    db = SessionLocal()
    count = 0

    try:
        if start_page == 1:
            db.execute(text("DELETE FROM sancoes_cepim"))
            db.commit()

        async for item in collector.coletar_sancoes_cepim(start_page):
            db.execute(text("""
                INSERT INTO sancoes_cepim (cnpj, nome, motivo, orgao_maximo)
                VALUES (:cnpj, :nome, :motivo, :orgao)
            """), {
                "cnpj": item["cnpj"], "nome": item["nome"],
                "motivo": item["motivo"], "orgao": item["orgao_maximo"],
            })
            count += 1
            if count % 100 == 0:
                db.commit()
                cp.update_progress("sancoes", "cepim",
                                   last_page=collector.current_page, total=count)
                logger.info("cepim_progresso", count=count)

        db.commit()
    finally:
        db.close()

    cp.mark_completed("sancoes", "cepim", total=count)
    logger.info("cepim_completo", total=count)


async def coletar_ceaf(cp: CheckpointManager):
    if cp.get_status("sancoes", "ceaf") == "completed":
        logger.info("ceaf_skip")
        return

    start_page = cp.get_last_page("sancoes", "ceaf") + 1
    cp.mark_started("sancoes", "ceaf")
    collector = CGUCollector()
    init_db()
    db = SessionLocal()
    count = 0

    try:
        if start_page == 1:
            db.execute(text("DELETE FROM sancoes_ceaf"))
            db.commit()

        async for item in collector.coletar_sancoes_ceaf(start_page):
            db.execute(text("""
                INSERT INTO sancoes_ceaf (cpf, nome, tipo_punicao,
                    orgao_lotacao, data_inicio, data_fim)
                VALUES (:cpf, :nome, :tipo, :orgao, :di, :df)
            """), {
                "cpf": _safe_str(item["cpf"]) or "",
                "nome": _safe_str(item["nome"]) or "",
                "tipo": _safe_str(item["tipo_punicao"]) or "",
                "orgao": _safe_str(item["orgao_lotacao"]) or "",
                "di": _parse_date(item.get("data_inicio")),
                "df": _parse_date(item.get("data_fim")),
            })
            count += 1
            if count % 100 == 0:
                db.commit()
                cp.update_progress("sancoes", "ceaf",
                                   last_page=collector.current_page, total=count)
                logger.info("ceaf_progresso", count=count)

        db.commit()
    finally:
        db.close()

    cp.mark_completed("sancoes", "ceaf", total=count)
    logger.info("ceaf_completo", total=count)


# ---------------------------------------------------------------------------
# Convênios
# ---------------------------------------------------------------------------
async def coletar_convenios(cp: CheckpointManager, ano: int | None = None):
    """Coleta convênios mês a mês (API limita período a 1 mês)."""
    import calendar
    collector = CGUCollector()
    anos = [ano] if ano else ANOS_CONVENIOS

    for a in anos:
        key = str(a)
        if cp.get_status("convenios", key) == "completed":
            logger.info("convenios_skip", ano=a)
            continue

        cp.mark_started("convenios", key)
        init_db()
        db = SessionLocal()
        count = 0

        # Verificar último mês processado para resume
        progress = cp.data.get("convenios", {}).get(key, {})
        start_month = progress.get("last_month", 1)

        try:
            for mes in range(start_month, 13):
                ultimo_dia = calendar.monthrange(a, mes)[1]
                data_ini = f"01/{mes:02d}/{a}"
                data_fim = f"{ultimo_dia}/{mes:02d}/{a}"
                logger.info("convenios_mes", ano=a, mes=mes)

                async for item in collector.coletar_convenios(data_ini, data_fim):
                    numero = item.get("numero_convenio")
                    if not numero:
                        continue

                    existe = db.execute(
                        text("SELECT id FROM convenios WHERE numero_convenio = :n"),
                        {"n": numero}
                    ).fetchone()
                    if existe:
                        continue

                    db.execute(text("""
                        INSERT INTO convenios (numero_convenio, situacao, orgao_concedente,
                            cpf_cnpj_convenente, nome_convenente, uf, municipio, objeto,
                            valor_convenio, valor_liberado, data_inicio, data_fim,
                            funcao, subfuncao)
                        VALUES (:num, :sit, :orgao, :cpf, :nome, :uf, :mun, :obj,
                                :val_conv, :val_lib, :di, :df, :func, :sfunc)
                    """), {
                        "num": numero, "sit": item["situacao"],
                        "orgao": item["orgao_concedente"],
                        "cpf": item["cpf_cnpj_convenente"],
                        "nome": item["nome_convenente"],
                        "uf": item["uf"], "mun": item["municipio"],
                        "obj": item["objeto"],
                        "val_conv": item["valor_convenio"],
                        "val_lib": item["valor_liberado"],
                        "di": _parse_date(item.get("data_inicio")),
                        "df": _parse_date(item.get("data_fim")),
                        "func": item["funcao"], "sfunc": item["subfuncao"],
                    })
                    count += 1
                    if count % 100 == 0:
                        db.commit()
                        cp.update_progress("convenios", key,
                                           last_page=collector.current_page,
                                           total=count, last_month=mes)
                        logger.info("convenios_progresso", ano=a, mes=mes, count=count)

                db.commit()
                cp.update_progress("convenios", key,
                                   last_page=0, total=count, last_month=mes + 1)
        finally:
            db.close()

        cp.mark_completed("convenios", key, total=count)
        logger.info("convenios_completo", ano=a, total=count)


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
async def main(resume: bool = False, tipo: str | None = None,
               ano: int | None = None):
    cp = CheckpointManager(path=CHECKPOINT_PATH)
    if not resume:
        cp.reset()

    logger.info("=" * 60)
    logger.info("INGESTÃO SANÇÕES/CONVÊNIOS — INÍCIO", resume=resume,
                tipo=tipo or "todos")
    logger.info("=" * 60)

    init_db()

    tarefas = {
        "ceis": lambda: coletar_ceis(cp),
        "cnep": lambda: coletar_cnep(cp),
        "cepim": lambda: coletar_cepim(cp),
        "ceaf": lambda: coletar_ceaf(cp),
        "convenios": lambda: coletar_convenios(cp, ano),
    }

    if tipo:
        tarefas_exec = {tipo: tarefas[tipo]}
    else:
        tarefas_exec = tarefas

    for nome, func in tarefas_exec.items():
        while True:
            try:
                logger.info(f"=== COLETANDO: {nome.upper()} ===")
                await func()
                break
            except KeyboardInterrupt:
                logger.warning("interrompido")
                raise
            except Exception as e:
                logger.error("erro", tipo=nome, erro=str(e)[:200])
                logger.info("aguardando_30s")
                await asyncio.sleep(30)

    logger.info("=" * 60)
    logger.info("INGESTÃO SANÇÕES/CONVÊNIOS — COMPLETA")
    stats()
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de sanções e convênios")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--tipo",
                        choices=["ceis", "cnep", "cepim", "ceaf", "convenios"])
    parser.add_argument("--ano", type=int, default=None,
                        help="Ano para convênios (ex: 2023)")
    args = parser.parse_args()
    asyncio.run(main(resume=args.resume, tipo=args.tipo, ano=args.ano))
