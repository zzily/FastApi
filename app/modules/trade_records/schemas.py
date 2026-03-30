from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TradeMarket, TradeSide


class TradeRecordRead(BaseModel):
    id: int
    symbol: str
    market: TradeMarket
    side: TradeSide
    traded_at: date
    pnl: float
    setup: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TradeRecordCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=255)
    market: TradeMarket = TradeMarket.stock
    side: TradeSide = TradeSide.long
    traded_at: date
    pnl: Decimal = Field(..., description="该笔交易净收益，可为正负零")
    setup: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None


class TradeRecordUpdate(BaseModel):
    symbol: Optional[str] = Field(None, min_length=1, max_length=255)
    market: Optional[TradeMarket] = None
    side: Optional[TradeSide] = None
    traded_at: Optional[date] = None
    pnl: Optional[Decimal] = Field(None, description="该笔交易净收益，可为正负零")
    setup: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None
