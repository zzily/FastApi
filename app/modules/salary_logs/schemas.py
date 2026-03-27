from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import IncomeSource


class SalaryLogRead(BaseModel):
    id: int
    amount: float
    amount_unused: float
    month: str
    source: IncomeSource
    remark: Optional[str] = None
    received_date: datetime

    model_config = ConfigDict(from_attributes=True)


class SalaryLogCreate(BaseModel):
    amount: float = Field(..., gt=0, description="实际到手金额")
    month: str = Field(..., examples=["2023-10"])
    source: IncomeSource = IncomeSource.salary
    remark: Optional[str] = None
    received_date: Optional[datetime] = None


class SalaryLogUpdate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="修改后的入账金额")
    source: IncomeSource
    received_date: Optional[datetime] = None
    remark: Optional[str] = None
    month: Optional[str] = None
