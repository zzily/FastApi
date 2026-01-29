from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from models import TransactionStatus, Category

# 基础模型
class TransactionBase(BaseModel):
    title: str
    amount_out: Decimal = Field(gt=0, description="垫付金额必须大于0")
    category: Category = Category.work
    remark: Optional[str] = None

# 创建记录时输入（只需要标题、金额、备注）
class TransactionCreate(TransactionBase):
    pass

# 报销时输入（只需填入老板给了多少钱）
class TransactionReimburse(BaseModel):
    amount_reimbursed: Decimal

# 接口返回模型
class TransactionResponse(TransactionBase):
    id: int
    amount_reimbursed: Decimal
    status: TransactionStatus
    created_at: datetime
    reimbursed_at: Optional[datetime]
    settled_at: Optional[datetime]
    
    # 计算字段：差价（老板给的 - 我垫的）
    @property
    def profit(self) -> Decimal:
        return self.amount_reimbursed - self.amount_out

    class Config:
        from_attributes = True

# 统计概览模型
class DebtSummary(BaseModel):
    father_holding: Decimal  # 父亲手里攒着的钱
    pending_reimbursement: Decimal  # 老板还没给的钱