from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models import SalaryLog, TransactionSettlement



def list_salary_logs(db: Session, skip: int = 0, limit: int = 100, available_only: bool = False) -> list[SalaryLog]:
    query = db.query(SalaryLog)
    if available_only:
        query = query.filter(SalaryLog.amount_unused > 0)
    return query.order_by(desc(SalaryLog.id)).offset(skip).limit(limit).all()



def get_salary_log(db: Session, salary_log_id: int) -> SalaryLog | None:
    return db.get(SalaryLog, salary_log_id)



def add_salary_log(db: Session, salary_log: SalaryLog) -> None:
    db.add(salary_log)



def delete_salary_log(db: Session, salary_log: SalaryLog) -> None:
    db.delete(salary_log)



def count_linked_settlements(db: Session, salary_log_id: int) -> int:
    return db.query(func.count(TransactionSettlement.id)).filter(
        TransactionSettlement.salary_log_id == salary_log_id
    ).scalar() or 0
