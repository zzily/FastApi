from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.responses import ok
from app.modules.salary_logs import schemas, service

router = APIRouter(prefix="/salary_logs", tags=["2. 入账 (资金池)"])


@router.get("/", response_model=List[schemas.SalaryLogRead])
def read_salary_logs(
    skip: int = 0,
    limit: int = settings.default_page_limit,
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    return service.list_salary_logs(db, skip=skip, limit=limit, available_only=available_only)


@router.post("/")
def create_salary_log(item: schemas.SalaryLogCreate, db: Session = Depends(get_db)):
    salary_log = service.create_salary_log(db, item)
    return ok("成功保存回款记录", {"id": salary_log.id})


@router.put("/{salary_log_id}", response_model=schemas.SalaryLogRead)
def update_salary_log(salary_log_id: int, item: schemas.SalaryLogUpdate, db: Session = Depends(get_db)):
    return service.update_salary_log(db, salary_log_id, item)


@router.delete("/{salary_log_id}")
def delete_salary_log(salary_log_id: int, db: Session = Depends(get_db)):
    service.delete_salary_log(db, salary_log_id)
    return ok("回款记录删除成功")
