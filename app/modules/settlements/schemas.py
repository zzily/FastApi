from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import IncomeSource, TransactionStatus


class SettlementActionResult(BaseModel):
    transaction_status: TransactionStatus
    salary_remaining: float
    transaction_remaining_debt: float


class SettlementRead(BaseModel):
    id: int
    amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettlementDetailRead(BaseModel):
    id: int
    transaction_id: int
    salary_log_id: int
    amount: float
    salary_month: str
    salary_source: IncomeSource
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SettleRequest(BaseModel):
    transaction_id: int
    salary_log_id: int
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="本次核销多少钱")
