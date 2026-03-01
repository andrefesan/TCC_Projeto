from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Parlamentar(Base):
    __tablename__ = "parlamentares"

    cod_autor = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    nome_civil = Column(String(200))
    partido = Column(String(20))
    uf = Column(String(2))
    legislaturas = Column(ARRAY(Integer))
    url_foto = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    emendas = relationship("Emenda", back_populates="parlamentar")
