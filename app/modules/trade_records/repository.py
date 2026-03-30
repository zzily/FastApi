from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import TradeRecord


def list_trade_records(db: Session, skip: int = 0, limit: int = 100) -> list[TradeRecord]:
    return (
        db.query(TradeRecord)
        .order_by(desc(TradeRecord.traded_at), desc(TradeRecord.id))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_trade_record(db: Session, trade_record_id: int) -> TradeRecord | None:
    return db.get(TradeRecord, trade_record_id)


def add_trade_record(db: Session, trade_record: TradeRecord) -> None:
    db.add(trade_record)


def delete_trade_record(db: Session, trade_record: TradeRecord) -> None:
    db.delete(trade_record)
