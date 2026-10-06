import hashlib
import json
from collections import defaultdict
from decimal import Decimal

from app.core.exceptions import BusinessRuleError
from app.core.time import now_local
from app.models import (
    ExpenseCategory,
    LedgerRestore,
    SalaryLog,
    TradeRecord,
    Transaction,
    TransactionSettlement,
)
from app.modules.ledger import repository
from app.modules.ledger.schemas import (
    BackupSnapshot,
    LedgerData,
    RestorePreview,
    RestoreResult,
)
from app.modules.transactions.service import calculate_transaction_status


def checksum_for(ledger):
    encoded = json.dumps(
        ledger.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def export_backup(db):
    repository.lock_ledger(db)
    ledger = LedgerData.model_validate(repository.export_rows(db))
    return BackupSnapshot(
        exported_at=now_local(), ledger=ledger, checksum=checksum_for(ledger)
    )


def validate_snapshot(snapshot):
    if snapshot.checksum != checksum_for(snapshot.ledger):
        raise BusinessRuleError("备份校验失败，文件可能已被修改或损坏")
    maps = {}
    for name, rows in snapshot.ledger:
        keyed = {row.id: row for row in rows}
        if len(keyed) != len(rows):
            raise BusinessRuleError(f"备份包含重复记录：{name}")
        maps[name] = keyed
    names = set()
    for category in maps["expense_categories"].values():
        key = (category.name.strip(), category.kind)
        if not key[0] or key in names:
            raise BusinessRuleError("备份分类名称无效或重复")
        names.add(key)
    paid = defaultdict(lambda: Decimal("0"))
    used = defaultdict(lambda: Decimal("0"))
    for settlement in maps["settlements"].values():
        if (
            settlement.transaction_id not in maps["transactions"]
            or settlement.salary_log_id not in maps["salary_logs"]
        ):
            raise BusinessRuleError("备份核销记录缺少关联账单或收入")
        paid[settlement.transaction_id] += settlement.amount
        used[settlement.salary_log_id] += settlement.amount
    for transaction in maps["transactions"].values():
        if (
            not transaction.title.strip()
            or transaction.amount_reimbursed > transaction.amount_out
            or paid[transaction.id] != transaction.amount_reimbursed
        ):
            raise BusinessRuleError("备份账单金额与核销历史不一致")
        if transaction.status != calculate_transaction_status(
            transaction.amount_out, transaction.amount_reimbursed
        ):
            raise BusinessRuleError("备份账单状态与金额不一致")
        if transaction.expense_category_id is not None:
            category = maps["expense_categories"].get(transaction.expense_category_id)
            if not category or category.kind != transaction.category:
                raise BusinessRuleError("备份账单缺少正确的支出分类")
    for salary in maps["salary_logs"].values():
        if (
            salary.amount_unused > salary.amount
            or used[salary.id] != salary.amount - salary.amount_unused
        ):
            raise BusinessRuleError("备份收入余额与核销历史不一致")
    for trade in maps["trade_records"].values():
        for column in TradeRecord.__table__.columns:
            value = getattr(trade, column.name, None)
            if isinstance(value, Decimal):
                if not value.is_finite():
                    raise BusinessRuleError("备份交易金额不是有效数字")
                precision = getattr(column.type, "precision", None)
                scale = getattr(column.type, "scale", None)
                if precision and (
                    abs(value) >= Decimal(10) ** (precision - scale)
                    or value != value.quantize(Decimal(1).scaleb(-scale))
                ):
                    raise BusinessRuleError("备份交易数字超过数据库精度")
        if (trade.fees or 0) < 0 or (trade.slippage or 0) < 0:
            raise BusinessRuleError("备份交易成本不能为负")
    return {name: len(rows) for name, rows in snapshot.ledger}


def preview_restore(db, snapshot):
    counts = validate_snapshot(snapshot)
    already = repository.get_restore(db, snapshot.checksum) is not None
    existing = repository.financial_counts(db)
    return RestorePreview(
        counts=counts,
        existing_counts=existing,
        can_restore=already or not any(existing.values()),
        already_restored=already,
    )


def restore_backup(db, snapshot):
    counts = validate_snapshot(snapshot)
    try:
        repository.lock_ledger(db)
        previous = repository.get_restore(db, snapshot.checksum)
        if previous:
            return RestoreResult(counts=previous.counts, already_restored=True)
        if any(repository.financial_counts(db).values()):
            raise BusinessRuleError(
                "当前账本已有记录，请使用空账本恢复；现有数据不会被覆盖",
                status_code=409,
            )
        category_map = {}
        existing = {
            (row.name, row.kind): row for row in repository.existing_categories(db)
        }
        for item in snapshot.ledger.expense_categories:
            key = (item.name.strip(), item.kind)
            category = existing.get(key)
            if category is None:
                category = ExpenseCategory(
                    name=key[0], kind=item.kind, archived=item.archived
                )
                db.add(category)
                db.flush()
            category.archived = item.archived
            category_map[item.id] = category.id
        salary_map = {}
        for item in snapshot.ledger.salary_logs:
            values = item.model_dump(exclude={"id"})
            record = SalaryLog(**values)
            db.add(record)
            db.flush()
            salary_map[item.id] = record.id
        transaction_map = {}
        for item in snapshot.ledger.transactions:
            values = item.model_dump(exclude={"id"})
            values["expense_category_id"] = category_map.get(item.expense_category_id)
            record = Transaction(**values)
            db.add(record)
            db.flush()
            transaction_map[item.id] = record.id
        for item in snapshot.ledger.trade_records:
            db.add(TradeRecord(**item.model_dump(exclude={"id"})))
        for item in snapshot.ledger.settlements:
            values = item.model_dump(exclude={"id"})
            values["transaction_id"] = transaction_map[item.transaction_id]
            values["salary_log_id"] = salary_map[item.salary_log_id]
            db.add(TransactionSettlement(**values))
        db.add(
            LedgerRestore(
                checksum=snapshot.checksum, restored_at=now_local(), counts=counts
            )
        )
        db.commit()
        return RestoreResult(counts=counts, already_restored=False)
    except Exception:
        db.rollback()
        raise
