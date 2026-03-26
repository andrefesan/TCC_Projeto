"""Modelo para convênios do Poder Executivo Federal."""
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, TIMESTAMP, func
from app.database import Base


class Convenio(Base):
    __tablename__ = "convenios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_convenio = Column(String(50), unique=True)
    situacao = Column(String(100))
    orgao_concedente = Column(String(300))
    cpf_cnpj_convenente = Column(String(20), index=True)
    nome_convenente = Column(String(300))
    uf = Column(String(2), index=True)
    municipio = Column(String(200))
    objeto = Column(Text)
    valor_convenio = Column(Numeric(15, 2))
    valor_liberado = Column(Numeric(15, 2))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    funcao = Column(String(5), index=True)
    subfuncao = Column(String(5))
    created_at = Column(TIMESTAMP, server_default=func.now())
