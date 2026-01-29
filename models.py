import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Text, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# --- 枚举定义 ---
class TransactionStatus(str, enum.Enum):
    pending = "pending"                     # 还没给钱 (amount_reimbursed = 0)
    partially_settled = "partially_settled" # 给了点，没给完 (0 < amount_reimbursed < amount_out)
    settled = "settled"                     # 结清了 (amount_reimbursed >= amount_out)

class Category(str, enum.Enum):
    work = "work"
    personal = "personal"

# --- 1. 账单表 (债权) ---
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(Enum(Category), default=Category.work)
    
    # 账单总金额
    amount_out = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # 【核心字段】已结算金额 (通过核销记录累加更新)
    amount_reimbursed = Column(Numeric(10, 2), default=0.00)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, index=True)
    
    receipt_url = Column(String(512), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系：一笔账单可以有多次核销记录
    settlements = relationship("TransactionSettlement", back_populates="transaction")

    @property
    def amount_due(self):
        """还剩多少没还"""
        return self.amount_out - self.amount_reimbursed

# --- 2. 回款记录表 (资金池) ---
class SalaryLog(Base):
    __tablename__ = "salary_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 这笔回款的总额，比如 5000 元
    amount = Column(Numeric(10, 2), nullable=False)
    
    # 【辅助字段】这笔钱还剩多少没被分配 (方便你下次继续用这笔钱核销)
    amount_unused = Column(Numeric(10, 2), nullable=False)
    
    month = Column(String(20), nullable=False) # 比如 "2023-10"
    received_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关系：一笔回款可以核销多笔账单
    settlements = relationship("TransactionSettlement", back_populates="salary_log")

# --- 3. 核销关联表 (动作) ---
class TransactionSettlement(Base):
    __tablename__ = "transaction_settlements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 哪笔账单
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    # 用了哪笔回款
    salary_log_id = Column(Integer, ForeignKey("salary_logs.id"), nullable=False)
    
    # 这次核销了多少钱
    amount = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    # 建立双向关系
    transaction = relationship("Transaction", back_populates="settlements")
    salary_log = relationship("SalaryLog", back_populates="settlements")