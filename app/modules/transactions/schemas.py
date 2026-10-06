from datetime import date, datetime
from decimal import Decimal
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
    expense_category_id: int | None = None
    expense_category_name: str | None = None
    occurred_at: date
    occurred_at_inferred: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    title: str
    amount_out: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="垫付金额")
    category: Category = Category.work
    payment_salary_log_id: int | None = Field(None, gt=0)
    occurred_at: date | None = None
    expense_category_id: int | None = Field(None, gt=0)


class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount_out: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2, description="垫付金额")
    category: Optional[Category] = None
    occurred_at: date | None = None
    expense_category_id: int | None = Field(None, gt=0)
