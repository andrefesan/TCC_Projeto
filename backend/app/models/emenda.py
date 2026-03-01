from sqlalchemy import (
    Column, Integer, String, Text, Numeric, TIMESTAMP, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Emenda(Base):
    __tablename__ = "emendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_emenda = Column(String(50), unique=True)
    cod_autor = Column(Integer, ForeignKey("parlamentares.cod_autor"))
    nome_autor = Column(String(200))
    ano = Column(Integer, nullable=False)
    tipo_emenda = Column(String(100))
    funcao = Column(String(5))
    funcao_nome = Column(String(100))
    subfuncao = Column(String(5))
    subfuncao_nome = Column(String(100))
    programa = Column(String(10))
    acao = Column(String(20))
    localidade = Column(String(200))
    uf = Column(String(2))
    valor_empenhado = Column(Numeric(15, 2), default=0)
    valor_liquidado = Column(Numeric(15, 2), default=0)
    valor_pago = Column(Numeric(15, 2), default=0)
    descricao = Column(Text)
    embedding = Column(Vector(384))
    fonte = Column(String(50), default="Portal da Transparência")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    parlamentar = relationship("Parlamentar", back_populates="emendas")
    execucoes = relationship("Execucao", back_populates="emenda", cascade="all, delete-orphan")
