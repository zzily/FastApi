from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
from models import TransactionStatus, Category, IncomeSource


# --- Unified response model ---
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None


# --- Read models ---
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


# --- Create models ---
class TransactionCreate(BaseModel):
    title: str
    amount_out: float = Field(..., gt=0, description="垫付金额")
    category: Category = Category.work


class SalaryLogCreate(BaseModel):
    amount: float = Field(..., gt=0, description="实际到手金额")
    month: str = Field(..., example="2023-10")
    source: IncomeSource = IncomeSource.salary
    remark: Optional[str] = None
    received_date: Optional[datetime] = None


# --- Update models ---
class SalaryLogUpdate(BaseModel):
    amount: Decimal
    source: IncomeSource
    received_date: Optional[datetime] = None
    remark: Optional[str] = None
    month: Optional[str] = None


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount_out: Optional[float] = Field(None, gt=0, description="垫付金额")
    category: Optional[Category] = None


# --- Request models ---
class SettleRequest(BaseModel):
    transaction_id: int
    salary_log_id: int
    amount: float = Field(..., gt=0, description="本次核销多少钱")
