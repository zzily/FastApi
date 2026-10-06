from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.responses import ok
from app.core.schemas import ApiResponseSchema
from app.modules.expense_categories import schemas, service

router = APIRouter(prefix="/expense_categories", tags=["支出分类"])


@router.get("/", response_model=ApiResponseSchema[list[schemas.ExpenseCategoryRead]])
def list_categories(include_archived: bool = False, db: Session = Depends(get_db)):
    return ok("获取分类成功", service.list_categories(db, include_archived))


@router.post("/", response_model=ApiResponseSchema[schemas.ExpenseCategoryRead])
def create_category(
    payload: schemas.ExpenseCategoryCreate, db: Session = Depends(get_db)
):
    return ok("分类已创建", service.create_category(db, payload))


@router.put(
    "/{category_id}", response_model=ApiResponseSchema[schemas.ExpenseCategoryRead]
)
def update_category(
    category_id: int,
    payload: schemas.ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
):
    return ok("分类已更新", service.update_category(db, category_id, payload))


@router.delete(
    "/{category_id}", response_model=ApiResponseSchema[schemas.ExpenseCategoryRead]
)
def archive_category(category_id: int, db: Session = Depends(get_db)):
    return ok("分类已停用，历史账单保留", service.archive_category(db, category_id))
