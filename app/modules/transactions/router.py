from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.responses import ok
from app.core.schemas import ApiResponseSchema, IdPayload
from app.modules.transactions import schemas, service

router = APIRouter(prefix="/transactions", tags=["1. 记账 (债权)"])


@router.get("/", response_model=ApiResponseSchema[List[schemas.TransactionRead]])
def read_transactions(
    skip: int = 0,
    limit: int = settings.default_page_limit,
    unpaid_only: bool = False,
    db: Session = Depends(get_db),
):
    transactions = service.list_transactions(db, skip=skip, limit=limit, unpaid_only=unpaid_only)
    return ok("获取账单成功", transactions)


@router.post("/", response_model=ApiResponseSchema[IdPayload])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    transaction = service.create_transaction(db, item)
    return ok("成功保存账单", {"id": transaction.id})


@router.put("/{transaction_id}", response_model=ApiResponseSchema[schemas.TransactionRead])
def update_transaction(transaction_id: int, item: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    transaction = service.update_transaction(db, transaction_id, item)
    return ok("账单更新成功", transaction)


@router.delete("/{transaction_id}", response_model=ApiResponseSchema[IdPayload])
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    service.delete_transaction(db, transaction_id)
    return ok("账单删除成功", {"id": transaction_id})
