from sqlalchemy import Column, DateTime, Integer, JSON, String
from app.core.db import Base


class LedgerGuard(Base):
    __tablename__ = "ledger_guard"
    id = Column(Integer, primary_key=True)
    revision = Column(Integer, nullable=False, default=0)


class LedgerRestore(Base):
    __tablename__ = "ledger_restores"
    checksum = Column(String(64), primary_key=True)
    restored_at = Column(DateTime, nullable=False)
    counts = Column(JSON, nullable=False)
