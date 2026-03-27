from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import SalaryLog, Transaction, TransactionSettlement



def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)



def get_transaction_with_lock(db: Session, transaction_id: int) -> Transaction | None:
    return db.execute(
        select(Transaction).where(Transaction.id == transaction_id).with_for_update()
    ).scalar_one_or_none()



def get_salary_log_with_lock(db: Session, salary_log_id: int) -> SalaryLog | None:
    return db.execute(
        select(SalaryLog).where(SalaryLog.id == salary_log_id).with_for_update()
    ).scalar_one_or_none()



def get_settlement(db: Session, settlement_id: int) -> TransactionSettlement | None:
    return db.get(TransactionSettlement, settlement_id)



def add_settlement(db: Session, settlement: TransactionSettlement) -> None:
    db.add(settlement)



def delete_settlement(db: Session, settlement: TransactionSettlement) -> None:
    db.delete(settlement)



def list_transaction_settlements(db: Session, transaction_id: int) -> list[tuple[TransactionSettlement, SalaryLog | None]]:
    return (
        db.query(TransactionSettlement, SalaryLog)
        .outerjoin(SalaryLog, SalaryLog.id == TransactionSettlement.salary_log_id)
        .filter(TransactionSettlement.transaction_id == transaction_id)
        .order_by(desc(TransactionSettlement.created_at))
        .all()
    )
