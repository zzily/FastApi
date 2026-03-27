from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.domain.enums import IncomeSource


class SalaryLog(Base):
    __tablename__ = "salary_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    amount_unused = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    month = Column(String(20), nullable=False)
    source = Column(Enum(IncomeSource), default=IncomeSource.salary)
    remark = Column(String(255), nullable=True)
    received_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    settlements = relationship("TransactionSettlement", back_populates="salary_log")
