from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from pgvector.sqlalchemy import Vector
from app.database import Base


class ClassificacaoOrcamentaria(Base):
    __tablename__ = "classificacao_orcamentaria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    funcao = Column(String(5), nullable=False)
    funcao_nome = Column(String(100))
    subfuncao = Column(String(5))
    subfuncao_nome = Column(String(100))
    programa = Column(String(10))
    programa_nome = Column(String(200))
    descricao = Column(Text)
    embedding = Column(Vector(384))
    created_at = Column(TIMESTAMP, server_default=func.now())
