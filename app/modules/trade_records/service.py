from datetime import datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.models import TradeRecord
from app.modules.trade_records import repository
from app.modules.trade_records.schemas import TradeRecordCreate, TradeRecordUpdate

logger = get_logger(__name__)


def _normalize_symbol(value: str | None) -> str | None:
    if value is None:
        raise BusinessRuleError("交易标的不能为空")

    normalized = value.strip()
    if not normalized:
        raise BusinessRuleError("交易标的不能为空")

    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_decimal(value: Decimal | float | int | None) -> Decimal | None:
    if value is None:
        return None

    return Decimal(str(value))


def _require_value(value, message: str):
    if value is None:
        raise BusinessRuleError(message)

    return value


def _normalize_mistake_tags(values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []

    return [str(getattr(value, "value", value)) for value in values]


def _validate_time_range(entry_at: datetime | None, exit_at: datetime | None) -> None:
    if entry_at is not None and exit_at is not None and exit_at <= entry_at:
        raise BusinessRuleError("出场时间需要晚于入场时间")


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
    _validate_time_range(item.entry_at, item.exit_at)

    trade_record = TradeRecord(
        symbol=_normalize_symbol(item.symbol),
        market=item.market,
        side=item.side,
        traded_at=item.traded_at,
        pnl=_normalize_decimal(item.pnl) or Decimal("0"),
        setup=_normalize_optional_text(item.setup),
        note=_normalize_optional_text(item.note),
        entry_at=item.entry_at,
        exit_at=item.exit_at,
        entry_price=_normalize_decimal(item.entry_price),
        exit_price=_normalize_decimal(item.exit_price),
        position_size=_normalize_decimal(item.position_size),
        thesis=_normalize_optional_text(item.thesis),
        planned_stop=_normalize_decimal(item.planned_stop),
        planned_target=_normalize_decimal(item.planned_target),
        actual_stop=_normalize_decimal(item.actual_stop),
        actual_target=_normalize_decimal(item.actual_target),
        fees=_normalize_decimal(item.fees),
        slippage=_normalize_decimal(item.slippage),
        followed_plan=item.followed_plan,
        plan_clarity=item.plan_clarity,
        execution_quality=item.execution_quality,
        mistake_tags=_normalize_mistake_tags(item.mistake_tags),
        lesson=_normalize_optional_text(item.lesson),
        option_expiration=item.option_expiration,
        option_strike=_normalize_decimal(item.option_strike),
        option_right=item.option_right,
        option_structure=item.option_structure,
        option_premium_type=item.option_premium_type,
        option_max_risk=_normalize_decimal(item.option_max_risk),
        option_max_reward=_normalize_decimal(item.option_max_reward),
        option_delta=_normalize_decimal(item.option_delta),
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

    next_entry_at = item.entry_at if "entry_at" in provided_fields else trade_record.entry_at
    next_exit_at = item.exit_at if "exit_at" in provided_fields else trade_record.exit_at
    _validate_time_range(next_entry_at, next_exit_at)

    if "symbol" in provided_fields:
        trade_record.symbol = _normalize_symbol(item.symbol)
    if "market" in provided_fields:
        trade_record.market = _require_value(item.market, "交易市场不能为空")
    if "side" in provided_fields:
        trade_record.side = _require_value(item.side, "交易方向不能为空")
    if "traded_at" in provided_fields:
        trade_record.traded_at = _require_value(item.traded_at, "交易日期不能为空")
    if "pnl" in provided_fields:
        trade_record.pnl = _normalize_decimal(_require_value(item.pnl, "交易盈亏不能为空"))
    if "setup" in provided_fields:
        trade_record.setup = _normalize_optional_text(item.setup)
    if "note" in provided_fields:
        trade_record.note = _normalize_optional_text(item.note)
    if "entry_at" in provided_fields:
        trade_record.entry_at = item.entry_at
    if "exit_at" in provided_fields:
        trade_record.exit_at = item.exit_at
    if "entry_price" in provided_fields:
        trade_record.entry_price = _normalize_decimal(item.entry_price)
    if "exit_price" in provided_fields:
        trade_record.exit_price = _normalize_decimal(item.exit_price)
    if "position_size" in provided_fields:
        trade_record.position_size = _normalize_decimal(item.position_size)
    if "thesis" in provided_fields:
        trade_record.thesis = _normalize_optional_text(item.thesis)
    if "planned_stop" in provided_fields:
        trade_record.planned_stop = _normalize_decimal(item.planned_stop)
    if "planned_target" in provided_fields:
        trade_record.planned_target = _normalize_decimal(item.planned_target)
    if "actual_stop" in provided_fields:
        trade_record.actual_stop = _normalize_decimal(item.actual_stop)
    if "actual_target" in provided_fields:
        trade_record.actual_target = _normalize_decimal(item.actual_target)
    if "fees" in provided_fields:
        trade_record.fees = _normalize_decimal(item.fees)
    if "slippage" in provided_fields:
        trade_record.slippage = _normalize_decimal(item.slippage)
    if "followed_plan" in provided_fields:
        trade_record.followed_plan = item.followed_plan
    if "plan_clarity" in provided_fields:
        trade_record.plan_clarity = item.plan_clarity
    if "execution_quality" in provided_fields:
        trade_record.execution_quality = item.execution_quality
    if "mistake_tags" in provided_fields:
        trade_record.mistake_tags = _normalize_mistake_tags(item.mistake_tags)
    if "lesson" in provided_fields:
        trade_record.lesson = _normalize_optional_text(item.lesson)
    if "option_expiration" in provided_fields:
        trade_record.option_expiration = item.option_expiration
    if "option_strike" in provided_fields:
        trade_record.option_strike = _normalize_decimal(item.option_strike)
    if "option_right" in provided_fields:
        trade_record.option_right = item.option_right
    if "option_structure" in provided_fields:
        trade_record.option_structure = item.option_structure
    if "option_premium_type" in provided_fields:
        trade_record.option_premium_type = item.option_premium_type
    if "option_max_risk" in provided_fields:
        trade_record.option_max_risk = _normalize_decimal(item.option_max_risk)
    if "option_max_reward" in provided_fields:
        trade_record.option_max_reward = _normalize_decimal(item.option_max_reward)
    if "option_delta" in provided_fields:
        trade_record.option_delta = _normalize_decimal(item.option_delta)

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
