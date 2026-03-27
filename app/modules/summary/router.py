from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.responses import ok
from app.core.schemas import ApiResponseSchema
from app.modules.summary import schemas, service

router = APIRouter(tags=["4. 监控大盘"])


@router.get("/summary", response_model=ApiResponseSchema[schemas.SummaryResponse])
def get_dashboard(db: Session = Depends(get_db)):
    return ok("获取成功", service.get_dashboard(db))
