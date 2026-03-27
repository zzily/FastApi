from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from app.core.db import Base


class TransactionSettlement(Base):
    __tablename__ = "transaction_settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    salary_log_id = Column(Integer, ForeignKey("salary_logs.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    transaction = relationship("Transaction", back_populates="settlements")
    salary_log = relationship("SalaryLog", back_populates="settlements")
