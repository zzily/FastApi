import secrets
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.core.exceptions import BusinessRuleError
from app.core.responses import ok
from app.core.schemas import ApiResponseSchema
from app.modules.ledger import schemas, service

router = APIRouter(prefix="/ledger", tags=["账本"])


def require_restore_key(x_ledger_restore_key: str | None = Header(None)):
    if not settings.ledger_restore_token:
        raise BusinessRuleError("此账本尚未启用备份恢复", status_code=403)
    if not x_ledger_restore_key or not secrets.compare_digest(
        x_ledger_restore_key, settings.ledger_restore_token
    ):
        raise BusinessRuleError("恢复密钥不正确", status_code=401)


@router.get("/capabilities", response_model=ApiResponseSchema[dict])
def capabilities():
    return ok(
        "获取功能成功",
        {
            "transactionOccurrenceDate": True,
            "expenseCategories": True,
            "immediatePayment": True,
            "backups": True,
            "restore": bool(settings.ledger_restore_token),
        },
    )


@router.get("/backup", response_model=ApiResponseSchema[schemas.BackupSnapshot])
def export_backup(db: Session = Depends(get_db)):
    return ok("备份已生成", service.export_backup(db))


@router.post(
    "/restore/preview",
    response_model=ApiResponseSchema[schemas.RestorePreview],
    dependencies=[Depends(require_restore_key)],
)
def preview_restore(snapshot: schemas.BackupSnapshot, db: Session = Depends(get_db)):
    return ok("备份已校验", service.preview_restore(db, snapshot))


@router.post(
    "/restore",
    response_model=ApiResponseSchema[schemas.RestoreResult],
    dependencies=[Depends(require_restore_key)],
)
def restore_backup(snapshot: schemas.BackupSnapshot, db: Session = Depends(get_db)):
    return ok("账本恢复完成", service.restore_backup(db, snapshot))
