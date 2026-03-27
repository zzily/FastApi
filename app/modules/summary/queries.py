from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.enums import Category, IncomeSource
from app.models import SalaryLog, Transaction


def _transaction_month_expr(db: Session):
    dialect_name = db.bind.dialect.name if db.bind is not None else ""
    if dialect_name == "sqlite":
        return func.strftime("%Y-%m", Transaction.created_at)
    return func.date_format(Transaction.created_at, "%Y-%m")


def _apply_transaction_month_filter(query, db: Session, month: str | None):
    if month is None:
        return query
    return query.filter(_transaction_month_expr(db) == month)


def _apply_salary_month_filter(query, month: str | None):
    if month is None:
        return query
    return query.filter(SalaryLog.month == month)



def get_monthly_spending_by_category(db: Session, month: str | None = None):
    month_expr = _transaction_month_expr(db).label("month")
    query = (
        db.query(
            month_expr,
            Transaction.category,
            func.sum(Transaction.amount_out).label("total"),
        )
        .group_by(month_expr, Transaction.category)
    )
    return _apply_transaction_month_filter(query, db, month).all()



def get_monthly_income_by_source(db: Session, month: str | None = None):
    query = (
        db.query(
            SalaryLog.month,
            SalaryLog.source,
            func.sum(SalaryLog.amount).label("total"),
        )
        .group_by(SalaryLog.month, SalaryLog.source)
    )
    return _apply_salary_month_filter(query, month).all()



def get_category_totals(db: Session, month: str | None = None):
    query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount_out).label("total"),
        )
        .group_by(Transaction.category)
    )
    return _apply_transaction_month_filter(query, db, month).all()



def get_total_personal_spending(db: Session, month: str | None = None):
    query = (
        db.query(func.sum(Transaction.amount_out))
        .filter(Transaction.category == Category.personal)
    )
    return _apply_transaction_month_filter(query, db, month).scalar() or 0



def get_total_out(db: Session, month: str | None = None):
    query = db.query(func.sum(Transaction.amount_out))
    return _apply_transaction_month_filter(query, db, month).scalar() or 0



def get_total_income_by_source(db: Session, source: IncomeSource, month: str | None = None):
    query = db.query(func.sum(SalaryLog.amount)).filter(SalaryLog.source == source)
    return _apply_salary_month_filter(query, month).scalar() or 0



def get_ledger_outstanding(db: Session, month: str | None = None):
    query = db.query(func.sum(Transaction.amount_out - Transaction.amount_reimbursed))
    return _apply_transaction_month_filter(query, db, month).scalar() or 0



def get_wallet_unallocated(db: Session, month: str | None = None):
    query = db.query(func.sum(SalaryLog.amount_unused))
    return _apply_salary_month_filter(query, month).scalar() or 0
