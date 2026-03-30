from decimal import Decimal

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.models import TradeRecord
from app.modules.trade_records import repository
from app.modules.trade_records.schemas import TradeRecordCreate, TradeRecordUpdate

logger = get_logger(__name__)


def _normalize_symbol(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        raise BusinessRuleError("交易标的不能为空")

    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _handle_schema_error(error: Exception) -> None:
    raw_message = str(getattr(error, "orig", error)).lower()
    if "trade_records" in raw_message and ("doesn't exist" in raw_message or "no such table" in raw_message):
        raise AppError(
            "交易日志数据表尚未初始化，请先执行数据库迁移（alembic upgrade head）。",
            status_code=503,
        ) from error


def list_trade_records(db: Session, skip: int = 0, limit: int = 100) -> list[TradeRecord]:
    try:
        return repository.list_trade_records(db, skip=skip, limit=limit)
    except (ProgrammingError, OperationalError) as error:
        _handle_schema_error(error)
        raise


def create_trade_record(db: Session, item: TradeRecordCreate) -> TradeRecord:
    trade_record = TradeRecord(
        symbol=_normalize_symbol(item.symbol),
        market=item.market,
        side=item.side,
        traded_at=item.traded_at,
        pnl=Decimal(str(item.pnl)),
        setup=_normalize_optional_text(item.setup),
        note=_normalize_optional_text(item.note),
    )
    repository.add_trade_record(db, trade_record)

    try:
        db.commit()
        db.refresh(trade_record)
        return trade_record
    except (ProgrammingError, OperationalError) as error:
        db.rollback()
        _handle_schema_error(error)
        raise
    except Exception:
        db.rollback()
        logger.exception("保存交易记录失败")
        raise


def update_trade_record(db: Session, trade_record_id: int, item: TradeRecordUpdate) -> TradeRecord:
    try:
        trade_record = repository.get_trade_record(db, trade_record_id)
    except (ProgrammingError, OperationalError) as error:
        _handle_schema_error(error)
        raise
    if not trade_record:
        raise NotFoundError("交易记录不存在")

    provided_fields = item.model_fields_set

    if "symbol" in provided_fields:
        trade_record.symbol = _normalize_symbol(item.symbol)
    if "market" in provided_fields:
        trade_record.market = item.market
    if "side" in provided_fields:
        trade_record.side = item.side
    if "traded_at" in provided_fields:
        trade_record.traded_at = item.traded_at
    if "pnl" in provided_fields:
        trade_record.pnl = Decimal(str(item.pnl))
    if "setup" in provided_fields:
        trade_record.setup = _normalize_optional_text(item.setup)
    if "note" in provided_fields:
        trade_record.note = _normalize_optional_text(item.note)

    try:
        db.commit()
        db.refresh(trade_record)
        return trade_record
    except (ProgrammingError, OperationalError) as error:
        db.rollback()
        _handle_schema_error(error)
        raise
    except Exception:
        db.rollback()
        logger.exception("更新交易记录失败")
        raise


def delete_trade_record(db: Session, trade_record_id: int) -> None:
    try:
        trade_record = repository.get_trade_record(db, trade_record_id)
    except (ProgrammingError, OperationalError) as error:
        _handle_schema_error(error)
        raise
    if not trade_record:
        raise NotFoundError("交易记录不存在")

    try:
        repository.delete_trade_record(db, trade_record)
        db.commit()
    except (ProgrammingError, OperationalError) as error:
        db.rollback()
        _handle_schema_error(error)
        raise
    except Exception:
        db.rollback()
        logger.exception("删除交易记录失败")
        raise
