from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.responses import ok
from app.core.schemas import ApiResponseSchema, IdPayload
from app.modules.trade_records import schemas, service

router = APIRouter(prefix="/trade_records", tags=["5. 交易日志"])


@router.get("/", response_model=ApiResponseSchema[List[schemas.TradeRecordRead]])
def read_trade_records(
    skip: int = 0,
    limit: int = settings.default_page_limit,
    db: Session = Depends(get_db),
):
    trade_records = service.list_trade_records(db, skip=skip, limit=limit)
    return ok("获取交易记录成功", trade_records)


@router.post("/", response_model=ApiResponseSchema[IdPayload])
def create_trade_record(item: schemas.TradeRecordCreate, db: Session = Depends(get_db)):
    trade_record = service.create_trade_record(db, item)
    return ok("成功保存交易记录", {"id": trade_record.id})


@router.put("/{trade_record_id}", response_model=ApiResponseSchema[schemas.TradeRecordRead])
def update_trade_record(
    trade_record_id: int,
    item: schemas.TradeRecordUpdate,
    db: Session = Depends(get_db),
):
    trade_record = service.update_trade_record(db, trade_record_id, item)
    return ok("交易记录更新成功", trade_record)


@router.delete("/{trade_record_id}", response_model=ApiResponseSchema[IdPayload])
def delete_trade_record(trade_record_id: int, db: Session = Depends(get_db)):
    service.delete_trade_record(db, trade_record_id)
    return ok("交易记录删除成功", {"id": trade_record_id})
