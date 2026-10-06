from app.modules.ledger.repository import lock_ledger
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models import ExpenseCategory
from app.modules.expense_categories import repository


def list_categories(db, include_archived=False):
    return repository.list_categories(db, include_archived)


def _save(db, category):
    try:
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise BusinessRuleError("同类型的分类名称已存在")
    except Exception:
        db.rollback()
        raise


def create_category(db, payload):
    lock_ledger(db)
    name = payload.name.strip()
    if not name:
        raise BusinessRuleError("分类名称不能为空")
    category = ExpenseCategory(name=name, kind=payload.kind, archived=False)
    repository.add_category(db, category)
    return _save(db, category)


def update_category(db, category_id, payload):
    lock_ledger(db)
    category = repository.get_category(db, category_id)
    if not category:
        raise NotFoundError("分类不存在")
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise BusinessRuleError("分类名称不能为空")
        category.name = name
    if payload.archived is not None:
        category.archived = payload.archived
    return _save(db, category)


def archive_category(db, category_id):
    from app.modules.expense_categories.schemas import ExpenseCategoryUpdate

    return update_category(db, category_id, ExpenseCategoryUpdate(archived=True))
