"""Carrega dados dos arquivos JSON locais para o banco de dados."""
import json
import sys
from pathlib import Path

# Load .env from projeto/ directory
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.services.ingestion.cgu_collector import CGUCollector
from app.services.ingestion.normalizer import DataNormalizer
import structlog

logger = structlog.get_logger()

DADOS_DIR = Path(__file__).parent.parent.parent.parent / "dados"


def carregar_deputados(normalizer: DataNormalizer):
    """Carrega deputados do JSON local."""
    arquivo = DADOS_DIR / "deputados_consolidado.json"
    if not arquivo.exists():
        logger.error("arquivo_nao_encontrado", arquivo=str(arquivo))
        return

    with open(arquivo, encoding="utf-8") as f:
        deputados_raw = json.load(f)

    # Deduplica por cod_autor (mesmo deputado pode aparecer com partidos diferentes)
    unicos = {}
    for dep in deputados_raw:
        unicos[dep["id"]] = dep

    count = 0
    for dep in unicos.values():
        normalizer.upsert_parlamentar({
            "cod_autor": dep["id"],
            "nome": dep["nome"].upper(),
            "partido": dep.get("siglaPartido", ""),
            "uf": dep.get("siglaUf", ""),
            "url_foto": dep.get("urlFoto", ""),
            "legislaturas": [dep.get("idLegislatura", 57)],
        })
        count += 1
        if count % 100 == 0:
            normalizer.commit()

    normalizer.commit()
    logger.info("deputados_carregados", total=count)


def carregar_emendas(normalizer: DataNormalizer):
    """Carrega emendas dos JSONs locais (2020-2024)."""
    collector = CGUCollector()
    total = 0
    codigos_vistos = set()

    for ano in range(2020, 2025):
        arquivo = DADOS_DIR / "emendas_reais" / f"emendas_{ano}.json"
        if not arquivo.exists():
            logger.warning("arquivo_nao_encontrado", arquivo=str(arquivo))
            continue

        with open(arquivo, encoding="utf-8") as f:
            emendas_raw = json.load(f)

        count = 0
        skipped = 0
        for raw in emendas_raw:
            codigo = raw.get("codigoEmenda", "")
            # Skip emendas sem código válido ou duplicadas
            if not codigo or codigo == "S/I" or codigo in codigos_vistos:
                skipped += 1
                continue
            codigos_vistos.add(codigo)

            emenda_data = collector._normalizar_emenda(raw, ano)
            emenda_data = normalizer.vincular_autor(emenda_data)
            normalizer.inserir_emenda(emenda_data)
            count += 1
            if count % 500 == 0:
                normalizer.commit()
                logger.info("emendas_batch", ano=ano, processadas=count)

        normalizer.commit()
        total += count
        logger.info("emendas_ano_carregado", ano=ano, inseridas=count, ignoradas=skipped)

    logger.info("emendas_carregadas_total", total=total)


def main():
    logger.info("iniciando_carga_local", dados_dir=str(DADOS_DIR))

    init_db()
    db = SessionLocal()
    normalizer = DataNormalizer(db)

    try:
        carregar_deputados(normalizer)
        carregar_emendas(normalizer)
        logger.info("carga_local_completa")
    except Exception as e:
        logger.error("erro_carga", erro=str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
