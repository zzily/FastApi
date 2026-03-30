from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Enum, Integer, Numeric, String, Text, func

from app.core.db import Base
from app.domain.enums import TradeMarket, TradeSide


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
    created_at = Column(DateTime, server_default=func.now())
