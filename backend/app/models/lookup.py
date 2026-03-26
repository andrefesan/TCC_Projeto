"""Modelos de tabelas lookup para normalização de dados orçamentários."""
from sqlalchemy import Column, String, ForeignKey
from app.database import Base


class Funcao(Base):
    __tablename__ = "funcoes"
    codigo = Column(String(5), primary_key=True)
    nome = Column(String(200), nullable=False)


class Subfuncao(Base):
    __tablename__ = "subfuncoes"
    codigo = Column(String(5), primary_key=True)
    nome = Column(String(200), nullable=False)
    funcao_codigo = Column(String(5), ForeignKey("funcoes.codigo"))


class Programa(Base):
    __tablename__ = "programas"
    codigo = Column(String(10), primary_key=True)
    nome = Column(String(300))


class Acao(Base):
    __tablename__ = "acoes"
    codigo = Column(String(20), primary_key=True)
    nome = Column(String(300))


class Orgao(Base):
    __tablename__ = "orgaos"
    codigo = Column(String(20), primary_key=True)
    nome = Column(String(300))
    orgao_superior_codigo = Column(String(20))


class UnidadeGestora(Base):
    __tablename__ = "unidades_gestoras"
    codigo = Column(String(20), primary_key=True)
    nome = Column(String(300))
    orgao_codigo = Column(String(20), ForeignKey("orgaos.codigo"))


class CategoriaDespesa(Base):
    __tablename__ = "categorias_despesa"
    codigo = Column(String(10), primary_key=True)
    nome = Column(String(200))


class GrupoDespesa(Base):
    __tablename__ = "grupos_despesa"
    codigo = Column(String(10), primary_key=True)
    nome = Column(String(200))


class ElementoDespesa(Base):
    __tablename__ = "elementos_despesa"
    codigo = Column(String(10), primary_key=True)
    nome = Column(String(200))


class ModalidadeAplicacao(Base):
    __tablename__ = "modalidades_aplicacao"
    codigo = Column(String(10), primary_key=True)
    nome = Column(String(200))
