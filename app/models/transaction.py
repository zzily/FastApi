from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.domain.enums import Category, TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(Enum(Category), default=Category.work)
    amount_out = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    amount_reimbursed = Column(Numeric(10, 2), default=Decimal("0.00"))
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, index=True)
    receipt_url = Column(String(512), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    settlements = relationship("TransactionSettlement", back_populates="transaction")

    @property
    def amount_due(self):
        return self.amount_out - self.amount_reimbursed
