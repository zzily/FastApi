from app.modules.ledger.repository import lock_ledger
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



def build_transaction(db: Session, item: TransactionCreate) -> Transaction:
    if item.occurred_at and item.occurred_at > now_local().date():
        raise BusinessRuleError("发生日期不能晚于今天")
    validate_expense_category(db, item.expense_category_id, item.category)
    transaction = Transaction(
        title=item.title,
        expense_category_id=item.expense_category_id,
        occurred_at=item.occurred_at or now_local().date(),
        occurred_at_inferred=False,
        amount_out=Decimal(str(item.amount_out)),
        category=item.category,
        created_at=now_local(),
        amount_reimbursed=Decimal("0"),
        status=TransactionStatus.pending,
    )
    return transaction


def create_transaction(db: Session, item: TransactionCreate) -> Transaction:
    lock_ledger(db)
    if item.payment_salary_log_id is not None:
        from app.modules.settlements.service import create_paid_transaction
        return create_paid_transaction(db, item)
    transaction = build_transaction(db, item)
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
    lock_ledger(db)
    transaction = repository.get_transaction(db, transaction_id)
    if not transaction:
        raise NotFoundError("账单不存在")

    category_id = item.expense_category_id if "expense_category_id" in item.model_fields_set else getattr(transaction, "expense_category_id", None)
    category_kind = item.category if item.category is not None else transaction.category
    validate_expense_category(db, category_id, category_kind, current_id=getattr(transaction,"expense_category_id",None))
    if "expense_category_id" in item.model_fields_set:
        transaction.expense_category_id = item.expense_category_id

    if "occurred_at" in item.model_fields_set:
        if item.occurred_at is None:
            raise BusinessRuleError("发生日期不能为空")
        if item.occurred_at > now_local().date():
            raise BusinessRuleError("发生日期不能晚于今天")
        transaction.occurred_at = item.occurred_at
        transaction.occurred_at_inferred = False

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
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        logger.exception("更新账单失败")
        raise



def delete_transaction(db: Session, transaction_id: int) -> None:
    lock_ledger(db)
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


def validate_expense_category(db, category_id, kind, current_id=None):
    if category_id is None:
        return
    category = repository.get_expense_category(db, category_id)
    if not category or (category.archived and category_id != current_id):
        raise BusinessRuleError("分类不存在或已停用")
    if category.kind != kind:
        raise BusinessRuleError("分类类型与账单类型不一致")
