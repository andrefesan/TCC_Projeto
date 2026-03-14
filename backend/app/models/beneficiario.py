from sqlalchemy import (
    Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Beneficiario(Base):
    __tablename__ = "beneficiarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_emenda.id", ondelete="CASCADE"))
    codigo_pessoa = Column(String(20))
    nome = Column(String(300), nullable=False)
    tipo_pessoa = Column(String(2))  # 'PF' ou 'PJ'
    cpf_cnpj = Column(String(20))
    valor_recebido = Column(Numeric(15, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    documento = relationship("DocumentoEmenda", back_populates="beneficiarios")
