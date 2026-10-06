from sqlalchemy import Boolean, Column, Enum, Integer, String, UniqueConstraint
from app.core.db import Base
from app.domain.enums import Category


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = (
        UniqueConstraint("name", "kind", name="uq_expense_category_name_kind"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    kind = Column(Enum(Category), nullable=False, default=Category.personal)
    archived = Column(Boolean, nullable=False, default=False)
