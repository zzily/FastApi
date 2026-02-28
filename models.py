import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# --- Enum definitions ---
class TransactionStatus(str, enum.Enum):
    pending = "pending"                     # amount_reimbursed = 0
    partially_settled = "partially_settled" # 0 < amount_reimbursed < amount_out
    settled = "settled"                     # amount_reimbursed >= amount_out


class Category(str, enum.Enum):
    work = "work"
    personal = "personal"


class IncomeSource(str, enum.Enum):
    salary = "salary"
    reimbursement = "reimbursement"
    other = "other"


# --- 1. Transaction table ---
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(Enum(Category), default=Category.work)
    amount_out = Column(Numeric(10, 2), nullable=False, default=0.00)
    amount_reimbursed = Column(Numeric(10, 2), default=0.00)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, index=True)
    receipt_url = Column(String(512), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    settlements = relationship("TransactionSettlement", back_populates="transaction")

    @property
    def amount_due(self):
        """Remaining unpaid amount"""
        return self.amount_out - self.amount_reimbursed


# --- 2. Salary log table ---
class SalaryLog(Base):
    __tablename__ = "salary_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    amount_unused = Column(Numeric(10, 2), nullable=False)
    month = Column(String(20), nullable=False)
    source = Column(Enum(IncomeSource), default=IncomeSource.salary)
    remark = Column(String(255), nullable=True)
    received_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    settlements = relationship("TransactionSettlement", back_populates="salary_log")


# --- 3. Settlement table ---
class TransactionSettlement(Base):
    __tablename__ = "transaction_settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    salary_log_id = Column(Integer, ForeignKey("salary_logs.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    transaction = relationship("Transaction", back_populates="settlements")
    salary_log = relationship("SalaryLog", back_populates="settlements")
