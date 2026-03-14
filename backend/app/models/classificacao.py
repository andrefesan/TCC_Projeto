from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from app.database import Base
from app.models.compat import VectorType


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
    embedding = Column(VectorType)
    created_at = Column(TIMESTAMP, server_default=func.now())
