"""Modelos para favorecidos normalizados e vínculo documento-favorecido."""
from sqlalchemy import (
    Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.compat import VectorType


class Favorecido(Base):
    __tablename__ = "favorecidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf_cnpj = Column(String(20), unique=True, nullable=False)
    nome = Column(String(300))
    tipo_pessoa = Column(String(2))  # 'PF' ou 'PJ'
    uf = Column(String(2))
    created_at = Column(TIMESTAMP, server_default=func.now())
    embedding = Column(VectorType)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    documentos = relationship(
        "DocumentoFavorecido", back_populates="favorecido",
        cascade="all, delete-orphan",
    )


class DocumentoFavorecido(Base):
    __tablename__ = "documento_favorecido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(
        Integer, ForeignKey("documentos_emenda.id", ondelete="CASCADE"),
    )
    favorecido_id = Column(Integer, ForeignKey("favorecidos.id"))
    valor_recebido = Column(Numeric(15, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    favorecido = relationship("Favorecido", back_populates="documentos")
    documento = relationship("DocumentoEmenda", back_populates="favorecidos_rel")
