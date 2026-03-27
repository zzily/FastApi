from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.core.time import now_local
from app.models import SalaryLog
from app.modules.salary_logs import repository
from app.modules.salary_logs.schemas import SalaryLogCreate, SalaryLogUpdate

logger = get_logger(__name__)



def list_salary_logs(db: Session, skip: int = 0, limit: int = 100, available_only: bool = False) -> list[SalaryLog]:
    return repository.list_salary_logs(db, skip=skip, limit=limit, available_only=available_only)



def create_salary_log(db: Session, item: SalaryLogCreate) -> SalaryLog:
    amount_decimal = Decimal(str(item.amount))
    actual_date = item.received_date if item.received_date else now_local()

    salary_log = SalaryLog(
        amount=amount_decimal,
        amount_unused=amount_decimal,
        source=item.source,
        remark=item.remark,
        month=item.month,
        received_date=actual_date,
        created_at=now_local(),
    )
    repository.add_salary_log(db, salary_log)

    try:
        db.commit()
        db.refresh(salary_log)
        return salary_log
    except Exception:
        db.rollback()
        logger.exception("保存回款失败")
        raise



def update_salary_log(db: Session, salary_log_id: int, item: SalaryLogUpdate) -> SalaryLog:
    salary_log = repository.get_salary_log(db, salary_log_id)
    if not salary_log:
        raise NotFoundError("记录不存在")

    amount_used = salary_log.amount - salary_log.amount_unused
    if item.amount < amount_used:
        raise BusinessRuleError(
            f"金额修改失败！该笔资金已核销使用了 {amount_used} 元，新金额不能低于此数值。"
        )

    salary_log.source = item.source
    salary_log.remark = item.remark
    if item.month is not None:
        salary_log.month = item.month
    if item.received_date is not None:
        salary_log.received_date = item.received_date
    salary_log.amount = item.amount
    salary_log.amount_unused = item.amount - amount_used

    try:
        db.commit()
        db.refresh(salary_log)
        return salary_log
    except Exception:
        db.rollback()
        logger.exception("更新回款失败")
        raise



def delete_salary_log(db: Session, salary_log_id: int) -> None:
    salary_log = repository.get_salary_log(db, salary_log_id)
    if not salary_log:
        raise NotFoundError("记录不存在")

    settlement_count = repository.count_linked_settlements(db, salary_log_id)
    if settlement_count > 0:
        raise BusinessRuleError(
            f"该回款已被 {settlement_count} 条核销记录引用，无法直接删除。请先撤销相关核销。"
        )

    try:
        repository.delete_salary_log(db, salary_log)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("删除回款失败")
        raise
