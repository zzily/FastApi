from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Category, TransactionStatus


class TransactionRead(BaseModel):
    id: int
    title: str
    category: Category
    amount_out: float
    amount_reimbursed: float
    status: TransactionStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    title: str
    amount_out: float = Field(..., gt=0, description="垫付金额")
    category: Category = Category.work


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount_out: Optional[float] = Field(None, gt=0, description="垫付金额")
    category: Optional[Category] = None
