from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import models, schemas

# 数据库配置
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/finance_manager"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="父亲财务监管系统")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 业务接口 ---

@app.post("/transactions/", response_model=schemas.TransactionResponse, tags=["1. 登记环节"])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """步骤1：看到亲属卡扣款，你录入一笔垫付记录"""
    db_item = models.Transaction(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.patch("/transactions/{tid}/reimburse", response_model=schemas.TransactionResponse, tags=["2. 报销环节"])
def mark_reimbursed(tid: int, data: schemas.TransactionReimburse, db: Session = Depends(get_db)):
    """步骤2：老板把钱给父亲了，你更新这笔账，钱进入'父亲口袋'状态"""
    db_item = db.query(models.Transaction).filter(models.Transaction.id == tid).first()
    if not db_item:
        raise HTTPException(404, "账目未找到")
    
    db_item.amount_reimbursed = data.amount_reimbursed
    db_item.status = models.TransactionStatus.received_by_father
    db_item.reimbursed_at = datetime.now()
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.patch("/transactions/{tid}/settle", response_model=schemas.TransactionResponse, tags=["3. 回收环节"])
def mark_settled(tid: int, db: Session = Depends(get_db)):
    """步骤3：父亲把钱转给你了，点击结清"""
    db_item = db.query(models.Transaction).filter(models.Transaction.id == tid).first()
    if not db_item:
        raise HTTPException(404, "账目未找到")
    
    db_item.status = models.TransactionStatus.settled
    db_item.settled_at = datetime.now()
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/summary", response_model=schemas.DebtSummary, tags=["监控"])
def get_debt_summary(db: Session = Depends(get_db)):
    """核心监控：计算他手里现在应该有多少钱"""
    # 父亲已收报销但未交出的总额
    father_holding = db.query(func.sum(models.Transaction.amount_reimbursed)).filter(
        models.Transaction.status == models.TransactionStatus.received_by_father
    ).scalar() or 0
    
    # 已经垫付但老板还没给钱的总额
    pending_reimbursement = db.query(func.sum(models.Transaction.amount_out)).filter(
        models.Transaction.status == models.TransactionStatus.pending
    ).scalar() or 0
    
    return {
        "father_holding": father_holding,
        "pending_reimbursement": pending_reimbursement
    }