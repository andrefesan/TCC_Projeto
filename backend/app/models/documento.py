from sqlalchemy import (
    Column, Integer, String, Numeric, Date, Text, TIMESTAMP, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.compat import VectorType


class DocumentoEmenda(Base):
    __tablename__ = "documentos_emenda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emenda_id = Column(Integer, ForeignKey("emendas.id", ondelete="CASCADE"))
    codigo_documento = Column(String(50), unique=True, nullable=False)
    fase = Column(String(20))
    valor = Column(Numeric(15, 2), default=0)
    data_documento = Column(Date)
    tipo_documento = Column(String(100))
    observacao = Column(Text)

    # Detalhes do endpoint /despesas/documentos/{codigo}
    funcao = Column(String(200))
    subfuncao = Column(String(200))
    programa = Column(String(300))
    acao = Column(String(300))
    localizador_gasto = Column(String(300))
    especie = Column(String(100))
    categoria = Column(String(200))
    grupo_despesa = Column(String(200))
    elemento_despesa = Column(String(200))
    modalidade = Column(String(200))
    orgao = Column(String(200))
    orgao_superior = Column(String(200))
    unidade_gestora = Column(String(200))
    unidade_orcamentaria = Column(String(200))
    favorecido_nome = Column(String(300))
    favorecido_cpf_cnpj = Column(String(20))
    favorecido_uf = Column(String(2))
    numero_processo = Column(String(50))
    plano_orcamentario = Column(String(300))
    embedding = Column(VectorType)
    detalhes_coletados = Column(Integer, default=0)  # flag: 1 = detalhes já coletados

    created_at = Column(TIMESTAMP, server_default=func.now())

    emenda = relationship("Emenda", back_populates="documentos")
    beneficiarios = relationship(
        "Beneficiario", back_populates="documento", cascade="all, delete-orphan"
    )
    favorecidos_rel = relationship(
        "DocumentoFavorecido", back_populates="documento", cascade="all, delete-orphan"
    )
