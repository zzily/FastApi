from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.core.time import now_local
from app.domain.enums import TransactionStatus
from app.models import Transaction
from app.modules.transactions import repository
from app.modules.transactions.schemas import TransactionCreate, TransactionUpdate

logger = get_logger(__name__)



def calculate_transaction_status(amount_out: Decimal, amount_reimbursed: Decimal) -> TransactionStatus:
    if amount_reimbursed <= 0:
        return TransactionStatus.pending
    if amount_reimbursed >= amount_out:
        return TransactionStatus.settled
    return TransactionStatus.partially_settled



def list_transactions(db: Session, skip: int = 0, limit: int = 100, unpaid_only: bool = False) -> list[Transaction]:
    return repository.list_transactions(db, skip=skip, limit=limit, unpaid_only=unpaid_only)



def create_transaction(db: Session, item: TransactionCreate) -> Transaction:
    transaction = Transaction(
        title=item.title,
        amount_out=Decimal(str(item.amount_out)),
        category=item.category,
        created_at=now_local(),
        amount_reimbursed=Decimal("0"),
        status=TransactionStatus.pending,
    )
    repository.add_transaction(db, transaction)

    try:
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        logger.exception("保存账单失败")
        raise



def update_transaction(db: Session, transaction_id: int, item: TransactionUpdate) -> Transaction:
    transaction = repository.get_transaction(db, transaction_id)
    if not transaction:
        raise NotFoundError("账单不存在")

    if item.title is not None:
        transaction.title = item.title
    if item.amount_out is not None:
        transaction.amount_out = Decimal(str(item.amount_out))
    if item.category is not None:
        transaction.category = item.category

    remaining_debt = transaction.amount_out - transaction.amount_reimbursed
    if remaining_debt < 0:
        raise BusinessRuleError("更新后的垫付金额不能小于已还金额")

    transaction.status = calculate_transaction_status(transaction.amount_out, transaction.amount_reimbursed)

    try:
        db.commit()
        return transaction
    except Exception:
        db.rollback()
        logger.exception("更新账单失败")
        raise



def delete_transaction(db: Session, transaction_id: int) -> None:
    transaction = repository.get_transaction(db, transaction_id)
    if not transaction:
        raise NotFoundError("账单不存在")

    settlement_count = repository.count_linked_settlements(db, transaction_id)
    if settlement_count > 0:
        raise BusinessRuleError(
            f"该账单已有 {settlement_count} 条核销记录，无法直接删除。请先撤销相关核销。"
        )

    try:
        repository.delete_transaction(db, transaction)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("删除账单失败")
        raise
