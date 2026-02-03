from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from models import TransactionStatus, Category, IncomeSource

class SettlementRead(BaseModel):
    id: int
    amount: float
    created_at: datetime
    class Config:
        from_attributes = True

class TransactionRead(BaseModel):
    id: int
    title: str
    category: Category
    amount_out: float
    amount_reimbursed: float
    status: TransactionStatus
    created_at: datetime
    class Config:
        from_attributes = True

class SalaryLogRead(BaseModel):
    id: int
    amount: float
    amount_unused: float
    month: str
    source: IncomeSource
    remark: Optional[str] = None
    received_date: datetime
    class Config:
        from_attributes = True

# 请求参数模型
class TransactionCreate(BaseModel):
    title: str
    amount_out: float = Field(..., gt=0, description="垫付金额")
    category: Category = Category.work

class SalaryLogCreate(BaseModel):
    amount: float = Field(..., gt=0, description="实际到手金额")
    month: str = Field(..., example="2023-10")
    source: IncomeSource = IncomeSource.salary # 默认是工资，可选 reimbursement
    remark: Optional[str] = None
    # 新增字段，允许用户指定日期，如果不填则默认为 None (由后端处理为当前时间)
    received_date: Optional[datetime] = None

class SettleRequest(BaseModel):
    transaction_id: int
    salary_log_id: int
    amount: float = Field(..., gt=0, description="本次核销多少钱")

class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount_out: Optional[float] = Field(None, gt=0, description="垫付金额")
    category: Optional[Category] = None