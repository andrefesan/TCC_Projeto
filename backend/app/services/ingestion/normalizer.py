from sqlalchemy.orm import Session
from app.models.parlamentar import Parlamentar
from app.models.emenda import Emenda
import structlog

logger = structlog.get_logger()


class DataNormalizer:
    """Normaliza e persiste dados de múltiplas fontes no schema unificado."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_parlamentar(self, data: dict) -> Parlamentar:
        cod = data["cod_autor"]
        existing = self.db.get(Parlamentar, cod)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            return existing
        parl = Parlamentar(**data)
        self.db.add(parl)
        self.db.flush()
        return parl

    def inserir_emenda(self, data: dict) -> Emenda:
        existing = self.db.query(Emenda).filter_by(
            codigo_emenda=data.get("codigo_emenda")
        ).first()
        if existing:
            return existing
        emenda = Emenda(**data)
        self.db.add(emenda)
        self.db.flush()
        return emenda

    def vincular_autor(self, emenda_data: dict):
        """Vincula emenda ao parlamentar pelo nome (fuzzy match)."""
        nome = emenda_data.get("nome_autor", "").upper()
        parlamentar = self.db.query(Parlamentar).filter(
            Parlamentar.nome.ilike(f"%{nome}%")
        ).first()
        if parlamentar:
            emenda_data["cod_autor"] = parlamentar.cod_autor
        return emenda_data

    def recalcular_valores_de_documentos(self):
        """Recalcula valor_empenhado/liquidado/pago das emendas a partir dos documentos.

        A API /emendas da CGU às vezes retorna valores divergentes do portal.
        Os documentos de despesa (empenhos individuais) são mais confiáveis.
        Usa o MAIOR entre o valor atual e a soma dos documentos por fase.
        """
        from sqlalchemy import text

        # Empenhado: soma de documentos com fase contendo 'empenho'
        self.db.execute(text("""
            UPDATE emendas SET valor_empenhado = sub.total
            FROM (
                SELECT d.emenda_id, SUM(d.valor) AS total
                FROM documentos_emenda d
                WHERE LOWER(d.fase) LIKE '%empenho%'
                  AND d.valor > 0
                GROUP BY d.emenda_id
            ) sub
            WHERE emendas.id = sub.emenda_id
              AND sub.total > emendas.valor_empenhado
        """))

        # Liquidado: soma de documentos com fase contendo 'liquidação'/'liquidacao'
        self.db.execute(text("""
            UPDATE emendas SET valor_liquidado = sub.total
            FROM (
                SELECT d.emenda_id, SUM(d.valor) AS total
                FROM documentos_emenda d
                WHERE (LOWER(d.fase) LIKE '%liquida%')
                  AND d.valor > 0
                GROUP BY d.emenda_id
            ) sub
            WHERE emendas.id = sub.emenda_id
              AND sub.total > emendas.valor_liquidado
        """))

        # Pago: soma de documentos com fase contendo 'pagamento'
        self.db.execute(text("""
            UPDATE emendas SET valor_pago = sub.total
            FROM (
                SELECT d.emenda_id, SUM(d.valor) AS total
                FROM documentos_emenda d
                WHERE LOWER(d.fase) LIKE '%pagamento%'
                  AND d.valor > 0
                GROUP BY d.emenda_id
            ) sub
            WHERE emendas.id = sub.emenda_id
              AND sub.total > emendas.valor_pago
        """))

        self.db.commit()
        logger.info("valores_recalculados_de_documentos")

    def recalcular_valores_de_documentos_sqlite(self):
        """Versão SQLite da reconciliação (sem UPDATE ... FROM)."""
        from sqlalchemy import text

        # SQLite não suporta UPDATE ... FROM, usar subquery
        for fase, coluna in [
            ('%empenho%', 'valor_empenhado'),
            ('%liquida%', 'valor_liquidado'),
            ('%pagamento%', 'valor_pago'),
        ]:
            self.db.execute(text(f"""
                UPDATE emendas SET {coluna} = (
                    SELECT SUM(d.valor)
                    FROM documentos_emenda d
                    WHERE d.emenda_id = emendas.id
                      AND LOWER(d.fase) LIKE :fase
                      AND d.valor > 0
                )
                WHERE id IN (
                    SELECT d2.emenda_id
                    FROM documentos_emenda d2
                    WHERE LOWER(d2.fase) LIKE :fase
                      AND d2.valor > 0
                    GROUP BY d2.emenda_id
                    HAVING SUM(d2.valor) > (
                        SELECT {coluna} FROM emendas WHERE id = d2.emenda_id
                    )
                )
            """), {"fase": fase})

        self.db.commit()
        logger.info("valores_recalculados_de_documentos_sqlite")

    def commit(self):
        self.db.commit()
