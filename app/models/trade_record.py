from decimal import Decimal

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Integer, Numeric, String, Text, func

from app.core.db import Base
from app.domain.enums import (
    TradeExecutionQuality,
    TradeMarket,
    TradeOptionRight,
    TradeOptionStructure,
    TradePlanClarity,
    TradePremiumType,
    TradeSide,
)


class TradeRecord(Base):
    __tablename__ = "trade_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), nullable=False, index=True)
    market = Column(Enum(TradeMarket), default=TradeMarket.stock, nullable=False)
    side = Column(Enum(TradeSide), default=TradeSide.long, nullable=False)
    traded_at = Column(Date, nullable=False, index=True)
    pnl = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    setup = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    entry_at = Column(DateTime, nullable=True)
    exit_at = Column(DateTime, nullable=True)
    entry_price = Column(Numeric(18, 6), nullable=True)
    exit_price = Column(Numeric(18, 6), nullable=True)
    position_size = Column(Numeric(18, 4), nullable=True)
    thesis = Column(Text, nullable=True)
    planned_stop = Column(Numeric(18, 6), nullable=True)
    planned_target = Column(Numeric(18, 6), nullable=True)
    actual_stop = Column(Numeric(18, 6), nullable=True)
    actual_target = Column(Numeric(18, 6), nullable=True)
    fees = Column(Numeric(18, 4), nullable=True)
    slippage = Column(Numeric(18, 4), nullable=True)
    followed_plan = Column(Boolean, nullable=True)
    plan_clarity = Column(Enum(TradePlanClarity), nullable=True)
    execution_quality = Column(Enum(TradeExecutionQuality), nullable=True)
    mistake_tags = Column(JSON, nullable=False, default=list)
    lesson = Column(Text, nullable=True)
    option_expiration = Column(Date, nullable=True)
    option_strike = Column(Numeric(18, 6), nullable=True)
    option_right = Column(Enum(TradeOptionRight), nullable=True)
    option_structure = Column(Enum(TradeOptionStructure), nullable=True)
    option_premium_type = Column(Enum(TradePremiumType), nullable=True)
    option_max_risk = Column(Numeric(18, 4), nullable=True)
    option_max_reward = Column(Numeric(18, 4), nullable=True)
    option_delta = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
