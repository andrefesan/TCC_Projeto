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
        existing = self.db.query(Parlamentar).filter_by(
            cod_autor=data["cod_autor"]
        ).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            return existing
        parl = Parlamentar(**data)
        self.db.add(parl)
        return parl

    def inserir_emenda(self, data: dict) -> Emenda:
        existing = self.db.query(Emenda).filter_by(
            codigo_emenda=data.get("codigo_emenda")
        ).first()
        if existing:
            return existing
        emenda = Emenda(**data)
        self.db.add(emenda)
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

    def commit(self):
        self.db.commit()
