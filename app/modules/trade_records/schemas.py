from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    TradeExecutionQuality,
    TradeMarket,
    TradeMistakeType,
    TradeOptionRight,
    TradeOptionStructure,
    TradePlanClarity,
    TradePremiumType,
    TradeSide,
)


class TradeRecordRead(BaseModel):
    id: int
    symbol: str
    market: TradeMarket
    side: TradeSide
    traded_at: date
    pnl: float
    setup: Optional[str] = None
    note: Optional[str] = None
    entry_at: Optional[datetime] = None
    exit_at: Optional[datetime] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    position_size: Optional[float] = None
    thesis: Optional[str] = None
    planned_stop: Optional[float] = None
    planned_target: Optional[float] = None
    actual_stop: Optional[float] = None
    actual_target: Optional[float] = None
    fees: Optional[float] = None
    slippage: Optional[float] = None
    followed_plan: Optional[bool] = None
    plan_clarity: Optional[TradePlanClarity] = None
    execution_quality: Optional[TradeExecutionQuality] = None
    mistake_tags: list[TradeMistakeType] = Field(default_factory=list)
    lesson: Optional[str] = None
    option_expiration: Optional[date] = None
    option_strike: Optional[float] = None
    option_right: Optional[TradeOptionRight] = None
    option_structure: Optional[TradeOptionStructure] = None
    option_premium_type: Optional[TradePremiumType] = None
    option_max_risk: Optional[float] = None
    option_max_reward: Optional[float] = None
    option_delta: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TradeRecordCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=255)
    market: TradeMarket = TradeMarket.stock
    side: TradeSide = TradeSide.long
    traded_at: date
    pnl: Decimal = Field(..., description="该笔交易盈亏，可为正负零")
    setup: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None
    entry_at: Optional[datetime] = None
    exit_at: Optional[datetime] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    position_size: Optional[Decimal] = None
    thesis: Optional[str] = None
    planned_stop: Optional[Decimal] = None
    planned_target: Optional[Decimal] = None
    actual_stop: Optional[Decimal] = None
    actual_target: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    followed_plan: Optional[bool] = None
    plan_clarity: Optional[TradePlanClarity] = None
    execution_quality: Optional[TradeExecutionQuality] = None
    mistake_tags: list[TradeMistakeType] = Field(default_factory=list)
    lesson: Optional[str] = None
    option_expiration: Optional[date] = None
    option_strike: Optional[Decimal] = None
    option_right: Optional[TradeOptionRight] = None
    option_structure: Optional[TradeOptionStructure] = None
    option_premium_type: Optional[TradePremiumType] = None
    option_max_risk: Optional[Decimal] = None
    option_max_reward: Optional[Decimal] = None
    option_delta: Optional[Decimal] = None


class TradeRecordUpdate(BaseModel):
    symbol: Optional[str] = Field(None, min_length=1, max_length=255)
    market: Optional[TradeMarket] = None
    side: Optional[TradeSide] = None
    traded_at: Optional[date] = None
    pnl: Optional[Decimal] = Field(None, description="该笔交易盈亏，可为正负零")
    setup: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None
    entry_at: Optional[datetime] = None
    exit_at: Optional[datetime] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    position_size: Optional[Decimal] = None
    thesis: Optional[str] = None
    planned_stop: Optional[Decimal] = None
    planned_target: Optional[Decimal] = None
    actual_stop: Optional[Decimal] = None
    actual_target: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    followed_plan: Optional[bool] = None
    plan_clarity: Optional[TradePlanClarity] = None
    execution_quality: Optional[TradeExecutionQuality] = None
    mistake_tags: Optional[list[TradeMistakeType]] = None
    lesson: Optional[str] = None
    option_expiration: Optional[date] = None
    option_strike: Optional[Decimal] = None
    option_right: Optional[TradeOptionRight] = None
    option_structure: Optional[TradeOptionStructure] = None
    option_premium_type: Optional[TradePremiumType] = None
    option_max_risk: Optional[Decimal] = None
    option_max_reward: Optional[Decimal] = None
    option_delta: Optional[Decimal] = None
