from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import Category, IncomeSource, TransactionStatus
from app.modules.trade_records.schemas import TradeRecordRead

Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]


class BackupCategory(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=50)
    kind: Category
    archived: bool = False


class BackupTransaction(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    category: Category
    amount_out: PositiveMoney
    amount_reimbursed: Money
    status: TransactionStatus
    receipt_url: str | None = None
    remark: str | None = None
    occurred_at: date
    occurred_at_inferred: bool = False
    expense_category_id: int | None = Field(None, gt=0)
    created_at: datetime


class BackupSalary(BaseModel):
    id: int = Field(gt=0)
    amount: PositiveMoney
    amount_unused: Money
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    source: IncomeSource
    remark: str | None = None
    received_date: datetime
    created_at: datetime


class BackupSettlement(BaseModel):
    id: int = Field(gt=0)
    transaction_id: int = Field(gt=0)
    salary_log_id: int = Field(gt=0)
    amount: PositiveMoney
    created_at: datetime


class BackupTrade(TradeRecordRead):
    # Keep database precision instead of the usual float response boundary.
    pnl: Decimal
    fees: Decimal | None = None
    slippage: Decimal | None = None
    entry_price: Decimal | None = None
    exit_price: Decimal | None = None
    position_size: Decimal | None = None
    planned_stop: Decimal | None = None
    planned_target: Decimal | None = None
    actual_stop: Decimal | None = None
    actual_target: Decimal | None = None
    option_strike: Decimal | None = None
    option_max_risk: Decimal | None = None
    option_max_reward: Decimal | None = None
    option_delta: Decimal | None = None


class LedgerData(BaseModel):
    expense_categories: list[BackupCategory] = Field(max_length=10000)
    transactions: list[BackupTransaction] = Field(max_length=100000)
    salary_logs: list[BackupSalary] = Field(max_length=100000)
    trade_records: list[BackupTrade] = Field(max_length=100000)
    settlements: list[BackupSettlement] = Field(max_length=100000)


class BackupSnapshot(BaseModel):
    version: Literal[2] = 2
    exported_at: datetime
    ledger: LedgerData
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    model_config = ConfigDict(extra="ignore")


class RestorePreview(BaseModel):
    counts: dict[str, int]
    existing_counts: dict[str, int]
    can_restore: bool
    already_restored: bool


class RestoreResult(BaseModel):
    counts: dict[str, int]
    already_restored: bool
