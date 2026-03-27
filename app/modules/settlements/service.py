from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.core.time import now_local
from app.domain.enums import IncomeSource
from app.models import TransactionSettlement
from app.modules.settlements import repository
from app.modules.settlements.schemas import SettleRequest
from app.modules.transactions.service import calculate_transaction_status

logger = get_logger(__name__)



def settle_debt(db: Session, item: SettleRequest) -> dict:
    transaction = repository.get_transaction_with_lock(db, item.transaction_id)
    salary_log = repository.get_salary_log_with_lock(db, item.salary_log_id)

    if not transaction:
        raise NotFoundError("账单不存在")
    if not salary_log:
        raise NotFoundError("回款记录不存在")

    settle_amount = Decimal(str(item.amount))
    if salary_log.amount_unused < settle_amount:
        raise BusinessRuleError(
            f"资金不足！该笔回款仅剩 {salary_log.amount_unused} 元，无法核销 {settle_amount} 元"
        )

    remaining_debt = transaction.amount_out - transaction.amount_reimbursed
    if remaining_debt < settle_amount:
        raise BusinessRuleError(f"超额核销！该账单仅欠 {remaining_debt} 元")

    settlement_log = TransactionSettlement(
        transaction_id=transaction.id,
        salary_log_id=salary_log.id,
        amount=settle_amount,
        created_at=now_local(),
    )

    salary_log.amount_unused -= settle_amount
    transaction.amount_reimbursed += settle_amount
    transaction.status = calculate_transaction_status(transaction.amount_out, transaction.amount_reimbursed)
    repository.add_settlement(db, settlement_log)

    try:
        db.commit()
        return {
            "transaction_status": transaction.status,
            "salary_remaining": float(salary_log.amount_unused),
            "transaction_remaining_debt": float(transaction.amount_out - transaction.amount_reimbursed),
        }
    except Exception:
        db.rollback()
        logger.exception("核销失败")
        raise



def get_transaction_settlements(db: Session, transaction_id: int) -> list[dict]:
    transaction = repository.get_transaction(db, transaction_id)
    if not transaction:
        raise NotFoundError("账单不存在")

    records = repository.list_transaction_settlements(db, transaction_id)
    return [
        {
            "id": record.id,
            "transaction_id": record.transaction_id,
            "salary_log_id": record.salary_log_id,
            "amount": float(record.amount),
            "salary_month": salary_log.month if salary_log else "未知",
            "salary_source": salary_log.source if salary_log else IncomeSource.other,
            "created_at": record.created_at,
        }
        for record, salary_log in records
    ]



def undo_settlement(db: Session, settlement_id: int) -> dict:
    record = repository.get_settlement(db, settlement_id)
    if not record:
        raise NotFoundError("核销记录不存在")

    transaction = repository.get_transaction_with_lock(db, record.transaction_id)
    salary_log = repository.get_salary_log_with_lock(db, record.salary_log_id)

    if not transaction:
        raise NotFoundError("关联账单不存在")
    if not salary_log:
        raise NotFoundError("关联回款记录不存在")

    transaction.amount_reimbursed -= record.amount
    salary_log.amount_unused += record.amount

    if transaction.amount_reimbursed <= 0:
        transaction.amount_reimbursed = Decimal("0")
    transaction.status = calculate_transaction_status(transaction.amount_out, transaction.amount_reimbursed)

    try:
        repository.delete_settlement(db, record)
        db.commit()
        return {
            "transaction_status": transaction.status,
            "transaction_remaining_debt": float(transaction.amount_out - transaction.amount_reimbursed),
            "salary_remaining": float(salary_log.amount_unused),
        }
    except Exception:
        db.rollback()
        logger.exception("撤销核销失败")
        raise
