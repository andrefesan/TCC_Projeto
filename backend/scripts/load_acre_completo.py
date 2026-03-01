"""Carrega o universo completo de emendas do Acre no banco de dados.
- Faz UPSERT: atualiza emendas existentes (por codigo_emenda), insere novas.
- Carrega também os deputados do Acre.
- Mantém todos os dados já existentes de outros estados.
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.models.emenda import Emenda
from app.models.parlamentar import Parlamentar
from app.services.ingestion.cgu_collector import CGUCollector
import structlog

logger = structlog.get_logger()

DADOS_DIR = Path(__file__).parent.parent.parent / "infos" / "dados"


def carregar_deputados_acre(db):
    """Carrega/atualiza deputados do Acre."""
    arquivo = DADOS_DIR / "deputados_acre.json"
    if not arquivo.exists():
        logger.error("arquivo_nao_encontrado", arquivo=str(arquivo))
        return

    with open(arquivo, encoding="utf-8") as f:
        deputados = json.load(f)

    count_insert = 0
    count_update = 0
    for dep in deputados:
        cod = dep["id"]
        existing = db.query(Parlamentar).filter_by(cod_autor=cod).first()
        if existing:
            existing.nome = dep["nome"].upper()
            existing.partido = dep.get("siglaPartido", "")
            existing.uf = dep.get("siglaUf", "")
            existing.url_foto = dep.get("urlFoto", "")
            existing.legislaturas = [dep.get("idLegislatura", 57)]
            count_update += 1
        else:
            parl = Parlamentar(
                cod_autor=cod,
                nome=dep["nome"].upper(),
                partido=dep.get("siglaPartido", ""),
                uf=dep.get("siglaUf", ""),
                url_foto=dep.get("urlFoto", ""),
                legislaturas=[dep.get("idLegislatura", 57)],
            )
            db.add(parl)
            count_insert += 1

    db.commit()
    logger.info("deputados_acre", inseridos=count_insert, atualizados=count_update)


def carregar_emendas_acre(db):
    """Carrega/atualiza emendas do Acre (universo completo)."""
    arquivo = DADOS_DIR / "emendas_reais" / "emendas_acre_completo.json"
    if not arquivo.exists():
        logger.error("arquivo_nao_encontrado", arquivo=str(arquivo))
        return

    with open(arquivo, encoding="utf-8") as f:
        emendas_raw = json.load(f)

    collector = CGUCollector()
    count_insert = 0
    count_update = 0
    count_skip = 0

    for raw in emendas_raw:
        codigo = raw.get("codigoEmenda", "")
        if not codigo or codigo == "S/I":
            count_skip += 1
            continue

        ano = raw.get("ano", 0)
        emenda_data = collector._normalizar_emenda(raw, ano)

        # Vincular ao parlamentar pelo nome
        nome_autor = emenda_data.get("nome_autor", "").upper()
        if nome_autor:
            parlamentar = db.query(Parlamentar).filter(
                Parlamentar.nome.ilike(f"%{nome_autor}%")
            ).first()
            if parlamentar:
                emenda_data["cod_autor"] = parlamentar.cod_autor

        existing = db.query(Emenda).filter_by(codigo_emenda=codigo).first()
        if existing:
            # Upsert: atualiza campos (mantém embedding se existir)
            for key, value in emenda_data.items():
                if key != "embedding":
                    setattr(existing, key, value)
            count_update += 1
        else:
            emenda = Emenda(**emenda_data)
            db.add(emenda)
            count_insert += 1

        if (count_insert + count_update) % 100 == 0:
            db.commit()
            logger.info("batch", inseridas=count_insert, atualizadas=count_update)

    db.commit()
    logger.info(
        "emendas_acre_completo",
        inseridas=count_insert,
        atualizadas=count_update,
        ignoradas=count_skip,
    )


def main():
    logger.info("iniciando_carga_acre_completo")
    init_db()
    db = SessionLocal()

    try:
        carregar_deputados_acre(db)
        carregar_emendas_acre(db)
        logger.info("carga_acre_completa")
    except Exception as e:
        logger.error("erro_carga_acre", erro=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
