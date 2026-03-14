"""Ingestão robusta de dados do Acre — 3 fases sequenciais.

Fase 1: Emendas (coleta todas as emendas AC de 2020-2024)
Fase 2: Documentos (coleta documentos de cada emenda)
Fase 3: Beneficiários (coleta favorecidos de cada documento)

Uso:
    python scripts/run_ingestion_ac.py
    python scripts/run_ingestion_ac.py --resume
    python scripts/run_ingestion_ac.py --etapa emendas
    python scripts/run_ingestion_ac.py --etapa documentos
    python scripts/run_ingestion_ac.py --etapa beneficiarios
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db, engine
import app.models  # noqa: F401
from app.services.ingestion.cgu_collector import CGUCollector
from app.services.ingestion.camara_collector import CamaraCollector
from app.services.ingestion.normalizer import DataNormalizer
from app.models.documento import DocumentoEmenda
from app.models.beneficiario import Beneficiario
from app.utils.checkpoint import CheckpointManager
import structlog

logger = structlog.get_logger()

UF_FILTRO = "AC"
ANOS = [2020, 2021, 2022, 2023, 2024]
LEGISLATURAS = [56, 57]
CHECKPOINT_PATH = Path(__file__).parent.parent / "data" / "checkpoint_ac.json"
MAX_RETRIES = 3


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def stats():
    """Mostra contagens atuais do banco."""
    with engine.connect() as c:
        for t in ["parlamentares", "emendas", "documentos_emenda", "beneficiarios"]:
            count = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            logger.info(f"  {t}: {count:,}")


# ---------------------------------------------------------------------------
# Fase 1: Deputados (pré-requisito)
# ---------------------------------------------------------------------------
async def fase_deputados(cp: CheckpointManager):
    if cp.get_status("deputados", "all") == "completed":
        logger.info("deputados_skip")
        return

    cp.mark_started("deputados", "all")
    init_db()
    db = SessionLocal()
    normalizer = DataNormalizer(db)
    collector = CamaraCollector()
    total = 0

    try:
        for leg in LEGISLATURAS:
            logger.info("coletando_deputados", legislatura=leg)
            deputados = await collector.coletar_deputados(leg)
            for dep in deputados:
                normalizer.upsert_parlamentar(dep)
            normalizer.commit()
            total += len(deputados)
            logger.info("deputados_ok", legislatura=leg, count=len(deputados))
    finally:
        db.close()

    cp.mark_completed("deputados", "all", total=total)


# ---------------------------------------------------------------------------
# Fase 2: Emendas (apenas AC, todas de 2020-2024)
# ---------------------------------------------------------------------------
async def fase_emendas(cp: CheckpointManager):
    collector = CGUCollector()

    for ano in ANOS:
        key = str(ano)
        if cp.get_status("emendas", key) == "completed":
            logger.info("emendas_skip", ano=ano)
            continue

        start_page = cp.get_last_page("emendas", key) + 1
        cp.mark_started("emendas", key)
        logger.info("coletando_emendas_ac", ano=ano, start_page=start_page)

        init_db()
        db = SessionLocal()
        normalizer = DataNormalizer(db)
        count = 0

        try:
            async for emenda_data in collector.coletar_emendas(ano, start_page=start_page):
                if emenda_data.get("uf") != UF_FILTRO:
                    continue

                emenda_data = normalizer.vincular_autor(emenda_data)
                normalizer.inserir_emenda(emenda_data)
                count += 1

                if count % 100 == 0:
                    normalizer.commit()
                    cp.update_progress("emendas", key,
                                       last_page=collector.current_page, total=count)
                    logger.info("emendas_batch", ano=ano, count=count,
                                page=collector.current_page)

            normalizer.commit()
        finally:
            db.close()

        cp.mark_completed("emendas", key, total=count)
        logger.info("emendas_completas", ano=ano, total=count)


# ---------------------------------------------------------------------------
# Fase 3: Documentos (coleta documentos de cada emenda AC)
# ---------------------------------------------------------------------------
async def fase_documentos(cp: CheckpointManager):
    if cp.get_status("documentos", "all") == "completed":
        logger.info("documentos_skip")
        return

    init_db()
    db = SessionLocal()
    collector = CGUCollector()
    last_index = cp.get_value("documentos", "all", "last_index", 0)
    cp.mark_started("documentos", "all")

    try:
        # Buscar emendas AC que ainda não têm documentos
        result = db.execute(text("""
            SELECT e.id, e.codigo_emenda
            FROM emendas e
            LEFT JOIN documentos_emenda d ON d.emenda_id = e.id
            WHERE d.id IS NULL
              AND e.codigo_emenda IS NOT NULL
              AND e.uf = :uf
            ORDER BY e.id
        """), {"uf": UF_FILTRO})
        emendas = [(r.id, r.codigo_emenda) for r in result.fetchall()]

        total_emendas = len(emendas)
        logger.info("documentos_inicio", total_emendas=total_emendas, resumindo_de=last_index)

        total_docs = 0
        erros = 0

        for i, (emenda_id, codigo_emenda) in enumerate(emendas):
            if i < last_index:
                continue

            for tentativa in range(1, MAX_RETRIES + 1):
                try:
                    docs = await collector.coletar_documentos_emenda(codigo_emenda)

                    for doc_data in docs:
                        existe = db.execute(
                            text("SELECT id FROM documentos_emenda WHERE codigo_documento = :cod"),
                            {"cod": doc_data["codigo_documento"]}
                        ).fetchone()

                        if not existe:
                            doc = DocumentoEmenda(
                                emenda_id=emenda_id,
                                codigo_documento=doc_data["codigo_documento"],
                                fase=doc_data.get("fase"),
                                valor=doc_data.get("valor", 0),
                                data_documento=_parse_date(doc_data.get("data_documento")),
                                tipo_documento=doc_data.get("tipo_documento"),
                                observacao=doc_data.get("observacao"),
                            )
                            db.add(doc)
                            db.flush()
                            total_docs += 1

                    db.commit()
                    break  # sucesso

                except Exception as e:
                    db.rollback()
                    if tentativa < MAX_RETRIES:
                        wait = tentativa * 10
                        logger.warning("retry_doc", codigo=codigo_emenda,
                                       tentativa=tentativa, wait=wait, erro=str(e)[:80])
                        await asyncio.sleep(wait)
                    else:
                        erros += 1
                        logger.error("falha_doc", codigo=codigo_emenda, erro=str(e)[:120])

            # Progresso a cada 10 emendas
            pos = i + 1
            if pos % 10 == 0 or pos == total_emendas:
                pct = pos / total_emendas * 100 if total_emendas else 0
                logger.info("progresso_documentos",
                            pos=pos, total=total_emendas,
                            pct=f"{pct:.1f}%", docs=total_docs, erros=erros)
                cp.update_progress("documentos", "all",
                                   last_index=i, total_docs=total_docs, erros=erros)

        cp.mark_completed("documentos", "all", total=total_docs)
        logger.info("documentos_completos", docs=total_docs, erros=erros)

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fase 4: Detalhes dos documentos (endpoint /despesas/documentos/{codigo})
# ---------------------------------------------------------------------------
async def fase_detalhes(cp: CheckpointManager):
    if cp.get_status("detalhes", "all") == "completed":
        logger.info("detalhes_skip")
        return

    init_db()
    db = SessionLocal()
    collector = CGUCollector()
    last_index = cp.get_value("detalhes", "all", "last_index", 0)
    cp.mark_started("detalhes", "all")

    try:
        # Documentos AC sem detalhes coletados
        result = db.execute(text("""
            SELECT d.id, d.codigo_documento
            FROM documentos_emenda d
            JOIN emendas e ON e.id = d.emenda_id
            WHERE e.uf = :uf
              AND (d.detalhes_coletados IS NULL OR d.detalhes_coletados = 0)
            ORDER BY d.id
        """), {"uf": UF_FILTRO})
        documentos = [(r.id, r.codigo_documento) for r in result.fetchall()]

        total = len(documentos)
        logger.info("detalhes_inicio", total=total, resumindo_de=last_index)

        coletados = 0
        erros = 0

        for i, (doc_id, codigo_documento) in enumerate(documentos):
            if i < last_index:
                continue

            for tentativa in range(1, MAX_RETRIES + 1):
                try:
                    detalhe = await collector.coletar_detalhes_documento(codigo_documento)

                    if detalhe:
                        db.execute(text("""
                            UPDATE documentos_emenda SET
                                funcao = :funcao,
                                subfuncao = :subfuncao,
                                programa = :programa,
                                acao = :acao,
                                localizador_gasto = :localizador,
                                especie = :especie,
                                categoria = :categoria,
                                grupo_despesa = :grupo,
                                elemento_despesa = :elemento,
                                modalidade = :modalidade,
                                orgao = :orgao,
                                orgao_superior = :orgao_sup,
                                unidade_gestora = :ug,
                                unidade_orcamentaria = :uo,
                                favorecido_nome = :fav_nome,
                                favorecido_cpf_cnpj = :fav_cpf,
                                favorecido_uf = :fav_uf,
                                numero_processo = :processo,
                                plano_orcamentario = :plano,
                                detalhes_coletados = 1
                            WHERE id = :id
                        """), {
                            "funcao": detalhe.get("funcao", ""),
                            "subfuncao": detalhe.get("subfuncao", ""),
                            "programa": detalhe.get("programa", ""),
                            "acao": detalhe.get("acao", ""),
                            "localizador": detalhe.get("localizadorGasto", ""),
                            "especie": detalhe.get("especie", ""),
                            "categoria": detalhe.get("categoria", ""),
                            "grupo": detalhe.get("grupo", ""),
                            "elemento": detalhe.get("elemento", ""),
                            "modalidade": detalhe.get("modalidade", ""),
                            "orgao": detalhe.get("orgao", ""),
                            "orgao_sup": detalhe.get("orgaoSuperior", ""),
                            "ug": detalhe.get("ug", ""),
                            "uo": detalhe.get("uo", ""),
                            "fav_nome": detalhe.get("nomeFavorecido", ""),
                            "fav_cpf": detalhe.get("codigoFavorecido", ""),
                            "fav_uf": detalhe.get("ufFavorecido", ""),
                            "processo": detalhe.get("numeroProcesso", ""),
                            "plano": detalhe.get("planoOrcamentario", ""),
                            "id": doc_id,
                        })
                        coletados += 1
                    else:
                        # Sem detalhes, marcar como coletado para não tentar de novo
                        db.execute(text(
                            "UPDATE documentos_emenda SET detalhes_coletados = 1 WHERE id = :id"
                        ), {"id": doc_id})

                    db.commit()
                    break  # sucesso

                except Exception as e:
                    db.rollback()
                    if tentativa < MAX_RETRIES:
                        wait = tentativa * 10
                        logger.warning("retry_detalhe", codigo=codigo_documento,
                                       tentativa=tentativa, wait=wait, erro=str(e)[:80])
                        await asyncio.sleep(wait)
                    else:
                        erros += 1
                        logger.error("falha_detalhe", codigo=codigo_documento,
                                     erro=str(e)[:120])

            pos = i + 1
            if pos % 50 == 0 or pos == total:
                pct = pos / total * 100 if total else 0
                logger.info("progresso_detalhes",
                            pos=pos, total=total,
                            pct=f"{pct:.1f}%", coletados=coletados, erros=erros)
                cp.update_progress("detalhes", "all",
                                   last_index=i, coletados=coletados, erros=erros)

        cp.mark_completed("detalhes", "all", total=coletados)
        logger.info("detalhes_completos", coletados=coletados, erros=erros)

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fase 5: Beneficiários (coleta favorecidos de cada documento)
# ---------------------------------------------------------------------------
async def fase_beneficiarios(cp: CheckpointManager):
    if cp.get_status("beneficiarios", "all") == "completed":
        logger.info("beneficiarios_skip")
        return

    init_db()
    db = SessionLocal()
    collector = CGUCollector()
    last_index = cp.get_value("beneficiarios", "all", "last_index", 0)
    cp.mark_started("beneficiarios", "all")

    try:
        # Buscar documentos de emendas AC que ainda não têm beneficiários
        result = db.execute(text("""
            SELECT d.id, d.codigo_documento
            FROM documentos_emenda d
            JOIN emendas e ON e.id = d.emenda_id
            LEFT JOIN beneficiarios b ON b.documento_id = d.id
            WHERE b.id IS NULL
              AND e.uf = :uf
            ORDER BY d.id
        """), {"uf": UF_FILTRO})
        documentos = [(r.id, r.codigo_documento) for r in result.fetchall()]

        total_documentos = len(documentos)
        logger.info("beneficiarios_inicio", total_docs=total_documentos, resumindo_de=last_index)

        total_benef = 0
        erros = 0

        for i, (doc_id, codigo_documento) in enumerate(documentos):
            if i < last_index:
                continue

            for tentativa in range(1, MAX_RETRIES + 1):
                try:
                    beneficiarios = await collector.coletar_beneficiarios_documento(
                        codigo_documento
                    )

                    for b in beneficiarios:
                        db.add(Beneficiario(
                            documento_id=doc_id,
                            codigo_pessoa=b.get("codigo_pessoa"),
                            nome=b["nome"],
                            tipo_pessoa=b.get("tipo_pessoa"),
                            cpf_cnpj=b.get("cpf_cnpj"),
                            valor_recebido=b.get("valor_recebido", 0),
                        ))
                        total_benef += 1

                    db.commit()
                    break  # sucesso

                except Exception as e:
                    db.rollback()
                    if tentativa < MAX_RETRIES:
                        wait = tentativa * 10
                        logger.warning("retry_benef", codigo=codigo_documento,
                                       tentativa=tentativa, wait=wait, erro=str(e)[:80])
                        await asyncio.sleep(wait)
                    else:
                        erros += 1
                        logger.error("falha_benef", codigo=codigo_documento,
                                     erro=str(e)[:120])

            # Progresso a cada 20 documentos
            pos = i + 1
            if pos % 20 == 0 or pos == total_documentos:
                pct = pos / total_documentos * 100 if total_documentos else 0
                logger.info("progresso_beneficiarios",
                            pos=pos, total=total_documentos,
                            pct=f"{pct:.1f}%", benef=total_benef, erros=erros)
                cp.update_progress("beneficiarios", "all",
                                   last_index=i, total_benef=total_benef, erros=erros)

        cp.mark_completed("beneficiarios", "all", total=total_benef)
        logger.info("beneficiarios_completos", benef=total_benef, erros=erros)

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Orquestrador com auto-recuperação
# ---------------------------------------------------------------------------
async def main(resume: bool = False, etapa: str | None = None):
    cp = CheckpointManager(path=CHECKPOINT_PATH)
    if not resume:
        cp.reset()

    logger.info("=" * 60)
    logger.info("INGESTÃO ACRE — INÍCIO", resume=resume,
                etapa_unica=etapa or "todas")
    logger.info("=" * 60)

    init_db()

    etapas = {
        "deputados": fase_deputados,
        "emendas": fase_emendas,
        "documentos": fase_documentos,
        "detalhes": fase_detalhes,
        "beneficiarios": fase_beneficiarios,
    }

    if etapa:
        etapas_exec = {etapa: etapas[etapa]}
    else:
        etapas_exec = etapas

    for nome, func in etapas_exec.items():
        while True:
            try:
                logger.info(f"=== FASE: {nome.upper()} ===")
                await func(cp)
                break  # Sucesso — próxima fase
            except KeyboardInterrupt:
                logger.warning("interrompido_pelo_usuario",
                               checkpoint=str(CHECKPOINT_PATH))
                raise
            except Exception as e:
                logger.error("erro_fase", fase=nome, erro=str(e)[:200])
                logger.info("aguardando_30s_para_retry")
                await asyncio.sleep(30)
                logger.info("retomando_fase", fase=nome)

    logger.info("=" * 60)
    logger.info("INGESTÃO ACRE — COMPLETA")
    stats()
    logger.info("checkpoint", path=str(CHECKPOINT_PATH))
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão robusta — Acre")
    parser.add_argument("--resume", action="store_true",
                        help="Retomar do checkpoint")
    parser.add_argument("--etapa",
                        choices=["deputados", "emendas", "documentos", "detalhes", "beneficiarios"],
                        help="Executar apenas uma fase específica")
    args = parser.parse_args()

    asyncio.run(main(resume=args.resume, etapa=args.etapa))
