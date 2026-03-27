from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.enums import Category, IncomeSource
from app.models import SalaryLog, Transaction



def get_monthly_spending_by_category(db: Session):
    return (
        db.query(
            func.date_format(Transaction.created_at, "%Y-%m").label("month"),
            Transaction.category,
            func.sum(Transaction.amount_out).label("total"),
        )
        .group_by("month", Transaction.category)
        .all()
    )



def get_monthly_income_by_source(db: Session):
    return (
        db.query(
            SalaryLog.month,
            SalaryLog.source,
            func.sum(SalaryLog.amount).label("total"),
        )
        .group_by(SalaryLog.month, SalaryLog.source)
        .all()
    )



def get_category_totals(db: Session):
    return (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount_out).label("total"),
        )
        .group_by(Transaction.category)
        .all()
    )



def get_total_personal_spending(db: Session):
    return (
        db.query(func.sum(Transaction.amount_out))
        .filter(Transaction.category == Category.personal)
        .scalar()
        or 0
    )



def get_total_out(db: Session):
    return db.query(func.sum(Transaction.amount_out)).scalar() or 0



def get_total_income_by_source(db: Session, source: IncomeSource):
    return db.query(func.sum(SalaryLog.amount)).filter(SalaryLog.source == source).scalar() or 0



def get_ledger_outstanding(db: Session):
    return db.query(func.sum(Transaction.amount_out - Transaction.amount_reimbursed)).scalar() or 0



def get_wallet_unallocated(db: Session):
    return db.query(func.sum(SalaryLog.amount_unused)).scalar() or 0
