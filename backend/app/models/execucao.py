from sqlalchemy import Column, Integer, String, Numeric, Date, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Execucao(Base):
    __tablename__ = "execucao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emenda_id = Column(Integer, ForeignKey("emendas.id", ondelete="CASCADE"))
    data_movimento = Column(Date)
    valor = Column(Numeric(15, 2))
    fase = Column(String(20))  # 'empenho', 'liquidacao', 'pagamento'
    documento = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    emenda = relationship("Emenda", back_populates="execucoes")
