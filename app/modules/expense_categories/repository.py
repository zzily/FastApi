from sqlalchemy.orm import Session
from app.models import ExpenseCategory


def list_categories(db: Session, include_archived: bool = False):
    query = db.query(ExpenseCategory)
    if not include_archived:
        query = query.filter(ExpenseCategory.archived.is_(False))
    return query.order_by(ExpenseCategory.id).all()


def get_category(db: Session, category_id: int):
    return db.get(ExpenseCategory, category_id)


def add_category(db: Session, category: ExpenseCategory):
    db.add(category)
