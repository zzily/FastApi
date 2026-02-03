from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Transaction, TransactionStatus, SalaryLog, TransactionSettlement
from typing import List, Optional
from sqlalchemy import desc
import schemas

# 数据库配置
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://zzliy123:1RIZKR8PlDEUCxDZ@mysql6.sqlpub.com:3311/finance_manager"
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

@app.get("/transactions/", response_model=List[schemas.TransactionRead], tags=["1. 记账 (债权)"])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    unpaid_only: bool = False,  # 新增：是否只看未结清的
    db: Session = Depends(get_db)
):
    """
    获取账单列表。
    - unpaid_only=True: 只看 pending 和 partially_settled 的账单 (用于核销)
    - 默认按 ID 倒序排列 (最新的在最前)
    """
    query = db.query(Transaction)
    
    if unpaid_only:
        # 筛选状态不等于 settled 的
        query = query.filter(Transaction.status != TransactionStatus.settled)
        
    # 按 ID 倒序，最新的账单显示在最上面
    transactions = query.order_by(desc(Transaction.id)).offset(skip).limit(limit).all()
    return transactions

@app.get("/salary_logs/", response_model=List[schemas.SalaryLogRead], tags=["2. 入账 (资金池)"])
def read_salary_logs(
    skip: int = 0, 
    limit: int = 100,
    available_only: bool = False, # 新增：是否只看还有余额的
    db: Session = Depends(get_db)
):
    """
    获取资金池记录。
    - available_only=True: 只看 amount_unused > 0 的记录 (用于核销时选择资金来源)
    """
    query = db.query(SalaryLog)
    
    if available_only:
        # 只筛选还有剩余金额的记录
        query = query.filter(SalaryLog.amount_unused > 0)
        
    # 按 ID 倒序
    logs = query.order_by(desc(SalaryLog.id)).offset(skip).limit(limit).all()
    return logs

@app.post("/transactions/", response_model=schemas.TransactionRead, tags=["1. 记账 (债权)"])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """记录你垫付的钱"""
    db_txn = Transaction(
        title=item.title,
        amount_out=item.amount_out,
        category=item.category,
        amount_reimbursed=0, # 初始已还为0
        status=TransactionStatus.pending
    )
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn

@app.post("/salary_logs/", response_model=schemas.SalaryLogRead, tags=["2. 入账 (资金池)"])
def create_salary_log(item: schemas.SalaryLogCreate, db: Session = Depends(get_db)):
    """
    记录父亲收到的钱 (资金入池)。
    
    - amount: 这次收到了多少钱
    - amount_unused: 初始状态下，余额 = 总额 (因为还没开始核销)
    - received_date: 实际到账时间 (如果不填，默认是录入的当前时间)
    """
    
    # 确定实际到账时间
    actual_date = item.received_date if item.received_date else datetime.now()

    db_salary = SalaryLog(
        amount=item.amount,
        
        # 【核心概念】
        # 刚入账时，这笔钱完全没被分配，所以"未使用金额"等于"总金额"。
        # 随着你调用 /settle 接口，这个字段会不断减少，直到变为 0。
        amount_unused=item.amount, 
        source=item.source,
        remark=item.remark,
        month=item.month,
        received_date=actual_date
    )
    
    db.add(db_salary)
    db.commit()
    db.refresh(db_salary)
    return db_salary

@app.post("/settle", tags=["3. 核销 (还钱)"])
def settle_debt(item: schemas.SettleRequest, db: Session = Depends(get_db)):
    """
    【核心逻辑】用某笔回款，去填平某笔账单。
    系统会自动扣减资金池余额，增加账单已还金额，并更新状态。
    """
    # 1. 获取对象
    txn = db.query(Transaction).with_for_update().get(item.transaction_id)
    salary = db.query(SalaryLog).with_for_update().get(item.salary_log_id)

    if not txn:
        raise HTTPException(404, "账单不存在")
    if not salary:
        raise HTTPException(404, "回款记录不存在")

    # 2. 校验逻辑
    settle_amount = Decimal(str(item.amount)) # 转为 Decimal 防止精度丢失

    if salary.amount_unused < settle_amount:
        raise HTTPException(400, f"资金不足！该笔回款仅剩 {salary.amount_unused} 元，无法核销 {settle_amount} 元")
    
    remaining_debt = txn.amount_out - txn.amount_reimbursed
    if remaining_debt < settle_amount:
        raise HTTPException(400, f"超额核销！该账单仅欠 {remaining_debt} 元")

    # 3. 执行扣减 (原子操作)
    try:
        # A. 扣减资金池
        salary.amount_unused -= settle_amount
        
        # B. 增加账单已还金额
        txn.amount_reimbursed += settle_amount
        
        # C. 更新账单状态
        if txn.amount_out - txn.amount_reimbursed == 0:
            txn.status = TransactionStatus.settled
        else:
            txn.status = TransactionStatus.partially_settled

        # D. 插入核销记录
        settlement_log = TransactionSettlement(
            transaction_id=txn.id,
            salary_log_id=salary.id,
            amount=settle_amount
        )
        db.add(settlement_log)
        
        db.commit()
        return {
            "message": "核销成功",
            "transaction_status": txn.status,
            "salary_remaining": salary.amount_unused,
            "transaction_remaining_debt": txn.amount_out - txn.amount_reimbursed
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"核销失败: {str(e)}")

@app.get("/summary", tags=["4. 监控大盘"])
def get_dashboard(db: Session = Depends(get_db)):
    """
    【债权人终极监控】
    不管父亲的钱是工资还是老板报销，也不管他私吞了没。
    只计算：我出了多少？回了多少？还差多少？
    """
    
    # --- A. 宏观总账 (绝对真理) ---
    
    # 1. 你垫付的总金额 (你流出的钱)
    total_principal = db.query(func.sum(Transaction.amount_out)).scalar() or 0
    
    # 2. 父亲转给你的总金额 (你流入的钱 - 无论名义是工资还是加油费)
    total_received = db.query(func.sum(SalaryLog.amount)).scalar() or 0
    
    # 3. 实际净欠款
    # 正数 = 父亲还欠你的
    # 负数 = 父亲多转给你了 (或者你还没垫付那么多)
    net_debt = total_principal - total_received


    # --- B. 记账操作状态 (你的工作进度) ---
    
    # 4. 账单上显示的"未结清金额"
    # 这是你还没有点"settle"的所有账单总额
    ledger_outstanding = db.query(
        func.sum(Transaction.amount_out - Transaction.amount_reimbursed)
    ).scalar() or 0
    
    # 5. 资金池里的"闲置余额"
    # 父亲转给你了，但你还没分配到具体账单上的钱
    wallet_unallocated = db.query(func.sum(SalaryLog.amount_unused)).scalar() or 0

    return {
        "financial_status": {
            "description": "资金往来总览 (硬账)",
            "total_lent_by_you": float(total_principal),    # 你一共垫了多少
            "total_received_back": float(total_received),   # 一共回血多少
            "current_net_debt": float(net_debt),            # 【核心指标】还差多少平账
            "status": "父亲仍欠款" if net_debt > 0 else "已回本/有盈余"
        },
        "operational_status": {
            "description": "记账操作概览 (软账)",
            "bills_pending_settlement": float(ledger_outstanding), # 待核销的账单金额
            "cash_waiting_allocation": float(wallet_unallocated),  # 待分配的现金余额
            "action_needed": "有闲钱，快去销账(Settle)" if wallet_unallocated > 0 and ledger_outstanding > 0 else "暂无操作"
        }
    }