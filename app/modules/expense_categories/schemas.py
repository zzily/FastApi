from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import Category


class ExpenseCategoryRead(BaseModel):
    id: int
    name: str
    kind: Category
    archived: bool
    model_config = ConfigDict(from_attributes=True)


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    kind: Category = Category.personal


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    archived: bool | None = None
