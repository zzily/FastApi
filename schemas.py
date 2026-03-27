"""Compatibility imports for the legacy flat schema module."""

from typing import Any

from pydantic import BaseModel

from app.modules.salary_logs.schemas import SalaryLogCreate, SalaryLogRead, SalaryLogUpdate
from app.modules.settlements.schemas import SettleRequest, SettlementDetailRead, SettlementRead
from app.modules.transactions.schemas import TransactionCreate, TransactionRead, TransactionUpdate


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None


__all__ = [
    "ApiResponse",
    "TransactionCreate",
    "TransactionRead",
    "TransactionUpdate",
    "SalaryLogCreate",
    "SalaryLogRead",
    "SalaryLogUpdate",
    "SettleRequest",
    "SettlementRead",
    "SettlementDetailRead",
]
