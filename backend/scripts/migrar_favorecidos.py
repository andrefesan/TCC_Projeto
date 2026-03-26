"""Migra dados de favorecidos existentes (AC) para tabelas normalizadas.

Popula:
  - favorecidos (a partir de documentos_emenda.favorecido_cpf_cnpj)
  - documento_favorecido (vínculos)
  - funcoes, subfuncoes (a partir de emendas)
  - orgaos, unidades_gestoras (a partir de documentos_emenda)

Uso:
    python scripts/migrar_favorecidos.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db, engine
import app.models  # noqa: F401
import structlog

logger = structlog.get_logger()


def migrar_funcoes(db):
    """Popula tabelas funcoes e subfuncoes a partir de emendas existentes."""
    logger.info("migrando_funcoes")

    result = db.execute(text("""
        SELECT DISTINCT funcao, funcao_nome FROM emendas
        WHERE funcao IS NOT NULL AND funcao != '' AND funcao_nome IS NOT NULL
    """))
    count = 0
    for row in result.fetchall():
        db.execute(text(
            "INSERT OR IGNORE INTO funcoes (codigo, nome) VALUES (:c, :n)"
        ), {"c": row[0], "n": row[1]})
        count += 1
    db.commit()
    logger.info("funcoes_migradas", total=count)

    result = db.execute(text("""
        SELECT DISTINCT subfuncao, subfuncao_nome, funcao FROM emendas
        WHERE subfuncao IS NOT NULL AND subfuncao != ''
          AND subfuncao_nome IS NOT NULL
    """))
    count = 0
    for row in result.fetchall():
        db.execute(text(
            "INSERT OR IGNORE INTO subfuncoes (codigo, nome, funcao_codigo) "
            "VALUES (:c, :n, :f)"
        ), {"c": row[0], "n": row[1], "f": row[2]})
        count += 1
    db.commit()
    logger.info("subfuncoes_migradas", total=count)


def migrar_favorecidos(db):
    """Popula tabela favorecidos a partir de documentos_emenda existentes."""
    logger.info("migrando_favorecidos")

    result = db.execute(text("""
        SELECT DISTINCT favorecido_cpf_cnpj, favorecido_nome, favorecido_uf
        FROM documentos_emenda
        WHERE favorecido_cpf_cnpj IS NOT NULL AND favorecido_cpf_cnpj != ''
    """))

    count = 0
    for row in result.fetchall():
        cpf_cnpj = row[0].strip()
        nome = (row[1] or "").strip()
        uf = (row[2] or "").strip()
        limpo = cpf_cnpj.replace(".", "").replace("-", "").replace("/", "")
        tipo = "PJ" if len(limpo) > 11 else "PF"

        db.execute(text(
            "INSERT OR IGNORE INTO favorecidos (cpf_cnpj, nome, tipo_pessoa, uf) "
            "VALUES (:cpf, :nome, :tipo, :uf)"
        ), {"cpf": cpf_cnpj, "nome": nome, "tipo": tipo, "uf": uf})
        count += 1

        if count % 500 == 0:
            db.commit()
            logger.info("favorecidos_progresso", count=count)

    db.commit()
    logger.info("favorecidos_migrados", total=count)


def migrar_vinculos(db):
    """Popula documento_favorecido com vínculos existentes."""
    logger.info("migrando_vinculos")

    result = db.execute(text("""
        SELECT d.id, d.favorecido_cpf_cnpj
        FROM documentos_emenda d
        WHERE d.favorecido_cpf_cnpj IS NOT NULL AND d.favorecido_cpf_cnpj != ''
    """))

    count = 0
    for row in result.fetchall():
        doc_id = row[0]
        cpf_cnpj = row[1].strip()

        fav = db.execute(
            text("SELECT id FROM favorecidos WHERE cpf_cnpj = :cpf"),
            {"cpf": cpf_cnpj}
        ).fetchone()

        if fav:
            ja = db.execute(
                text("SELECT id FROM documento_favorecido "
                     "WHERE documento_id = :did AND favorecido_id = :fid"),
                {"did": doc_id, "fid": fav[0]}
            ).fetchone()

            if not ja:
                db.execute(text(
                    "INSERT INTO documento_favorecido (documento_id, favorecido_id) "
                    "VALUES (:did, :fid)"
                ), {"did": doc_id, "fid": fav[0]})
                count += 1

        if count % 500 == 0 and count > 0:
            db.commit()
            logger.info("vinculos_progresso", count=count)

    db.commit()
    logger.info("vinculos_migrados", total=count)


def migrar_orgaos(db):
    """Popula tabelas orgaos e unidades_gestoras a partir de documentos existentes."""
    logger.info("migrando_orgaos")

    # Órgãos superiores
    result = db.execute(text("""
        SELECT DISTINCT orgao_superior FROM documentos_emenda
        WHERE orgao_superior IS NOT NULL AND orgao_superior != ''
    """))
    count = 0
    for row in result.fetchall():
        val = row[0]
        if " - " in val:
            cod, nome = val.split(" - ", 1)
            db.execute(text(
                "INSERT OR IGNORE INTO orgaos (codigo, nome) VALUES (:c, :n)"
            ), {"c": cod.strip(), "n": nome.strip()})
            count += 1
    db.commit()
    logger.info("orgaos_superiores_migrados", total=count)

    # Órgãos
    result = db.execute(text("""
        SELECT DISTINCT orgao, orgao_superior FROM documentos_emenda
        WHERE orgao IS NOT NULL AND orgao != ''
    """))
    count = 0
    for row in result.fetchall():
        val = row[0]
        sup = row[1] or ""
        cod_sup = sup.split(" - ", 1)[0].strip() if " - " in sup else ""
        if " - " in val:
            cod, nome = val.split(" - ", 1)
            db.execute(text(
                "INSERT OR IGNORE INTO orgaos (codigo, nome, orgao_superior_codigo) "
                "VALUES (:c, :n, :s)"
            ), {"c": cod.strip(), "n": nome.strip(), "s": cod_sup})
            count += 1
    db.commit()
    logger.info("orgaos_migrados", total=count)


def main():
    init_db()
    db = SessionLocal()

    try:
        migrar_funcoes(db)
        migrar_favorecidos(db)
        migrar_vinculos(db)
        migrar_orgaos(db)

        # Contagens finais
        for t in ["funcoes", "subfuncoes", "favorecidos",
                   "documento_favorecido", "orgaos"]:
            count = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            logger.info(f"  {t}: {count:,}")

    finally:
        db.close()

    logger.info("MIGRAÇÃO COMPLETA")


if __name__ == "__main__":
    main()
