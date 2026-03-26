"""Modelos para cadastros de sanções (CEIS, CNEP, CEPIM, CEAF)."""
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, TIMESTAMP, func
from app.database import Base


class SancaoCEIS(Base):
    __tablename__ = "sancoes_ceis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf_cnpj = Column(String(20), nullable=False, index=True)
    nome = Column(String(300))
    tipo_sancao = Column(String(200))
    orgao_sancionador = Column(String(300))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    fundamentacao = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class SancaoCNEP(Base):
    __tablename__ = "sancoes_cnep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf_cnpj = Column(String(20), nullable=False, index=True)
    nome = Column(String(300))
    tipo_sancao = Column(String(200))
    orgao_sancionador = Column(String(300))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    valor_multa = Column(Numeric(15, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())


class SancaoCEPIM(Base):
    __tablename__ = "sancoes_cepim"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(20), nullable=False, index=True)
    nome = Column(String(300))
    motivo = Column(Text)
    orgao_maximo = Column(String(300))
    created_at = Column(TIMESTAMP, server_default=func.now())


class SancaoCEAF(Base):
    __tablename__ = "sancoes_ceaf"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(14), nullable=False, index=True)
    nome = Column(String(300))
    tipo_punicao = Column(String(200))
    orgao_lotacao = Column(String(300))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    created_at = Column(TIMESTAMP, server_default=func.now())
