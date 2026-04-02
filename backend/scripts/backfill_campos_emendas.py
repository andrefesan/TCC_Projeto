"""Backfill de campos faltantes nas emendas a partir dos JSONs locais.

Campos atualizados:
  - valor_liquidado (nunca era salvo)
  - valor_resto_inscrito, valor_resto_cancelado, valor_resto_pago (novos)
  - numero_emenda (novo)

Não precisa da API — lê direto dos arquivos JSON já coletados.

Uso:
    python scripts/backfill_campos_emendas.py
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal, init_db
import structlog

logger = structlog.get_logger()

DADOS_DIR = Path(__file__).parent.parent.parent.parent / "Dados" / "dados"


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


def main():
    init_db()
    db = SessionLocal()

    # Garantir que colunas novas existem (SQLite ALTER TABLE)
    is_sqlite = "sqlite" in str(db.bind.url)
    if is_sqlite:
        for col, tipo in [
            ("valor_resto_inscrito", "NUMERIC(15,2) DEFAULT 0"),
            ("valor_resto_cancelado", "NUMERIC(15,2) DEFAULT 0"),
            ("valor_resto_pago", "NUMERIC(15,2) DEFAULT 0"),
            ("numero_emenda", "VARCHAR(20)"),
        ]:
            try:
                db.execute(text(f"ALTER TABLE emendas ADD COLUMN {col} {tipo}"))
                db.commit()
                logger.info("coluna_adicionada", coluna=col)
            except Exception:
                db.rollback()  # já existe

    total_atualizado = 0

    for ano in range(2020, 2025):
        arquivo = DADOS_DIR / "emendas_reais" / f"emendas_{ano}.json"
        if not arquivo.exists():
            logger.warning("arquivo_nao_encontrado", arquivo=str(arquivo))
            continue

        with open(arquivo, encoding="utf-8") as f:
            emendas_raw = json.load(f)

        count = 0
        for raw in emendas_raw:
            codigo = raw.get("codigoEmenda", "")
            if not codigo or codigo == "S/I":
                continue

            val_liq = _parse_valor(raw.get("valorLiquidado", "0"))
            val_ri = _parse_valor(raw.get("valorRestoInscrito", "0"))
            val_rc = _parse_valor(raw.get("valorRestoCancelado", "0"))
            val_rp = _parse_valor(raw.get("valorRestoPago", "0"))
            num = raw.get("numeroEmenda", "")

            db.execute(text("""
                UPDATE emendas SET
                    valor_liquidado = :val_liq,
                    valor_resto_inscrito = :val_ri,
                    valor_resto_cancelado = :val_rc,
                    valor_resto_pago = :val_rp,
                    numero_emenda = :num
                WHERE codigo_emenda = :codigo
            """), {
                "val_liq": val_liq,
                "val_ri": val_ri,
                "val_rc": val_rc,
                "val_rp": val_rp,
                "num": num,
                "codigo": codigo,
            })
            count += 1

            if count % 1000 == 0:
                db.commit()

        db.commit()
        total_atualizado += count
        logger.info("ano_processado", ano=ano, emendas=count)

    logger.info("backfill_campos_completo", total=total_atualizado)

    # Verificação rápida
    result = db.execute(text("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN valor_liquidado > 0 THEN 1 ELSE 0 END) as com_liquidado,
               SUM(CASE WHEN valor_resto_inscrito > 0 THEN 1 ELSE 0 END) as com_resto
        FROM emendas
    """))
    row = result.fetchone()
    logger.info("verificacao",
                total=row[0],
                com_liquidado=row[1],
                com_resto=row[2])

    db.close()


if __name__ == "__main__":
    main()
