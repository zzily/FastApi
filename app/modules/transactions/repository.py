from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.domain.enums import TransactionStatus
from app.models import Transaction, TransactionSettlement



def list_transactions(db: Session, skip: int = 0, limit: int = 100, unpaid_only: bool = False) -> list[Transaction]:
    query = db.query(Transaction)
    if unpaid_only:
        query = query.filter(Transaction.status != TransactionStatus.settled)
    return query.order_by(desc(Transaction.id)).offset(skip).limit(limit).all()



def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)



def add_transaction(db: Session, transaction: Transaction) -> None:
    db.add(transaction)



def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)



def count_linked_settlements(db: Session, transaction_id: int) -> int:
    return db.query(func.count(TransactionSettlement.id)).filter(
        TransactionSettlement.transaction_id == transaction_id
    ).scalar() or 0
