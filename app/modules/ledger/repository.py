from sqlalchemy import func, update
from app.models import (
    ExpenseCategory,
    LedgerGuard,
    LedgerRestore,
    SalaryLog,
    TradeRecord,
    Transaction,
    TransactionSettlement,
)

FINANCIAL_MODELS = {
    "transactions": Transaction,
    "salary_logs": SalaryLog,
    "trade_records": TradeRecord,
    "settlements": TransactionSettlement,
}
ALL_MODELS = {"expense_categories": ExpenseCategory, **FINANCIAL_MODELS}


def lock_ledger(db):
    # The no-op write serializes all financial writes, including SQLite transactions.
    result = db.execute(
        update(LedgerGuard)
        .where(LedgerGuard.id == 1)
        .values(revision=LedgerGuard.revision)
    )
    if result.rowcount != 1:
        raise RuntimeError("账本迁移未完成")


def export_rows(db):
    return {
        name: [
            {
                column.name: getattr(record, column.name)
                for column in model.__table__.columns
            }
            for record in db.query(model).order_by(model.id).all()
        ]
        for name, model in ALL_MODELS.items()
    }


def financial_counts(db):
    return {
        name: db.query(func.count(model.id)).scalar() or 0
        for name, model in FINANCIAL_MODELS.items()
    }


def get_restore(db, checksum):
    return db.get(LedgerRestore, checksum)


def existing_categories(db):
    return db.query(ExpenseCategory).all()
