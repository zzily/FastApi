from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.responses import ok
from app.modules.settlements import schemas, service

router = APIRouter(tags=["3. 核销 (还钱)"])


@router.post("/settle")
def settle_debt(item: schemas.SettleRequest, db: Session = Depends(get_db)):
    result = service.settle_debt(db, item)
    return ok("核销成功", result)


@router.get("/transactions/{transaction_id}/settlements")
def get_transaction_settlements(transaction_id: int, db: Session = Depends(get_db)):
    result = service.get_transaction_settlements(db, transaction_id)
    return ok("获取成功", result)


@router.delete("/settlements/{settlement_id}")
def undo_settlement(settlement_id: int, db: Session = Depends(get_db)):
    result = service.undo_settlement(db, settlement_id)
    return ok("撤销成功", result)
