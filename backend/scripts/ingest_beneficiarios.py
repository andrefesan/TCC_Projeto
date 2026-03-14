"""Script de ingestão de documentos e beneficiários das emendas."""
import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db
from app.services.ingestion.cgu_collector import CGUCollector
from app.models.documento import DocumentoEmenda
from app.models.beneficiario import Beneficiario
import structlog

logger = structlog.get_logger()


def _parse_date(date_str):
    """Converte string de data (dd/mm/yyyy ou yyyy-mm-dd) para date object."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


async def ingerir_beneficiarios(
    batch_size: int = 100,
    limit: int | None = None,
    start_index: int = 0,
    on_batch_commit=None,
):
    """Coleta documentos e beneficiários para todas as emendas no banco.

    Args:
        batch_size: Número de emendas processadas por commit.
        limit: Limitar a N emendas (para testes). None = todas.
        start_index: Índice da emenda para retomar (0 = início).
        on_batch_commit: Callback(i, total_docs, total_benef) chamado a cada batch.
    """
    init_db()
    db = SessionLocal()
    collector = CGUCollector()

    try:
        # Buscar emendas que ainda não têm documentos coletados
        query = """
            SELECT e.id, e.codigo_emenda
            FROM emendas e
            LEFT JOIN documentos_emenda d ON d.emenda_id = e.id
            WHERE d.id IS NULL AND e.codigo_emenda IS NOT NULL
            ORDER BY e.id
        """
        if limit:
            query += f" LIMIT {int(limit)}"

        result = db.execute(text(query))
        emendas = [(row.id, row.codigo_emenda) for row in result.fetchall()]

        logger.info("emendas_para_processar", total=len(emendas),
                     retomando_de=start_index)

        total_docs = 0
        total_benef = 0

        for i, (emenda_id, codigo_emenda) in enumerate(emendas, 1):
            if i < start_index:
                continue

            try:
                # 1. Coletar documentos da emenda
                documentos = await collector.coletar_documentos_emenda(codigo_emenda)

                for doc_data in documentos:
                    # Verificar se documento já existe
                    existe = db.execute(
                        text("SELECT id FROM documentos_emenda WHERE codigo_documento = :cod"),
                        {"cod": doc_data["codigo_documento"]}
                    ).fetchone()

                    if existe:
                        doc_id = existe.id
                    else:
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
                        doc_id = doc.id
                        total_docs += 1

                    # 2. Coletar beneficiários do documento
                    # Verificar se já existem beneficiários para este documento
                    benef_existentes = db.execute(
                        text("SELECT COUNT(*) FROM beneficiarios WHERE documento_id = :did"),
                        {"did": doc_id}
                    ).scalar()

                    if benef_existentes > 0:
                        continue

                    beneficiarios = await collector.coletar_beneficiarios_documento(
                        doc_data["codigo_documento"]
                    )

                    for benef_data in beneficiarios:
                        benef = Beneficiario(
                            documento_id=doc_id,
                            codigo_pessoa=benef_data.get("codigo_pessoa"),
                            nome=benef_data["nome"],
                            tipo_pessoa=benef_data.get("tipo_pessoa"),
                            cpf_cnpj=benef_data.get("cpf_cnpj"),
                            valor_recebido=benef_data.get("valor_recebido", 0),
                        )
                        db.add(benef)
                        total_benef += 1

            except Exception as e:
                db.rollback()
                logger.warning("erro_emenda", codigo=codigo_emenda, erro=str(e))
                continue

            # Commit em batches
            if i % batch_size == 0:
                db.commit()
                logger.info("batch_commit",
                             processadas=i, total=len(emendas),
                             docs=total_docs, benef=total_benef)
                if on_batch_commit:
                    on_batch_commit(i, total_docs, total_benef)

        # Commit final
        db.commit()
        logger.info("ingestao_beneficiarios_completa",
                     emendas=len(emendas), documentos=total_docs,
                     beneficiarios=total_benef)
        return {"emendas": len(emendas), "documentos": total_docs,
                "beneficiarios": total_benef}

    except Exception as e:
        db.rollback()
        logger.error("erro_ingestao_beneficiarios", erro=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de beneficiários")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Tamanho do batch para commit")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limitar a N emendas (para testes)")
    args = parser.parse_args()

    asyncio.run(ingerir_beneficiarios(
        batch_size=args.batch_size,
        limit=args.limit,
    ))
