from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Transaction, TransactionStatus, SalaryLog, TransactionSettlement, Category, IncomeSource
from typing import List, Optional
from sqlalchemy import desc
from fastapi.middleware.cors import CORSMiddleware
import time
from fastapi import Request
import schemas
from datetime import datetime
import pytz



# 数据库配置
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://4Azm2c71xKGJzVb.root:G8Ch4jZmQgOGeLKA@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/finance_manager?ssl_verify_cert=true&ssl_verify_identity=true"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


app = FastAPI(title="父亲财务监管系统")

# 允许跨域请求 (方便手机和平板访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 允许任何来源（手机、平板、其他电脑）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

BEIJING_TZ = pytz.timezone("Asia/Shanghai")
PERSONAL_INCOME_SOURCES = [IncomeSource.salary, IncomeSource.other]  # 生活循环收入来源（不含报销款）
BUSINESS_CATEGORIES = [category for category in Category if category != Category.personal]
ACTION_USE_SALARY_FOR_PERSONAL = "使用工资收入核销个人消费"
ACTION_USE_REIMBURSEMENT_FOR_BUSINESS = "使用报销款平公账"

# --- 计时中间件 --- 
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 1. 记录开始时间
    start_time = time.time()
    
    # 2. 处理请求 (调用具体的接口函数)
    response = await call_next(request)
    
    # 3. 记录结束时间并计算耗时
    process_time = time.time() - start_time
    
    # 4. 【关键步骤】将耗时添加到响应头 (Response Headers) 中
    # 这样你在浏览器 F12 的 Network 面板里也能看到这个值
    response.headers["X-Process-Time"] = str(process_time)
    
    # 5. 【可选】打印日志到控制台 (Zeabur 日志里能看到)
    # 格式：[方法] 路径 - 耗时秒数
    print(f"Checking Performance: {request.method} {request.url.path} - took {process_time:.4f} secs")
    
    return response

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
    # 有时数据库或上一操作可能会留下 None 项（导致 FastAPI 在序列化时抛出 ResponseValidationError），
    # 这里做一次保护性过滤，避免把 None 返回给客户端
    logs = [log for log in logs if log is not None]
    return logs

@app.post("/transactions/", tags=["1. 记账 (债权)"])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """记录你垫付的钱"""
    amount_out_decimal = Decimal(str(item.amount_out))
    db_txn = Transaction(
        title=item.title,
        amount_out=amount_out_decimal,
        category=item.category,
        created_at=datetime.now(BEIJING_TZ),
        amount_reimbursed=Decimal("0"), # 初始已还为0
        status=TransactionStatus.pending
    )
    try:
        db.add(db_txn)
        db.commit()
        return "成功保存账单"
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"保存账单失败: {str(e)}")

@app.post("/salary_logs/", tags=["2. 入账 (资金池)"])
def create_salary_log(item: schemas.SalaryLogCreate, db: Session = Depends(get_db)):
    """
    记录父亲收到的钱 (资金入池)。
    
    - amount: 这次收到了多少钱
    - amount_unused: 初始状态下，余额 = 总额 (因为还没开始核销)
    - received_date: 实际到账时间 (如果不填，默认是录入的当前时间)
    """
    
    # 确定实际到账时间
    actual_date = item.received_date if item.received_date else datetime.now(BEIJING_TZ)

    # 使用 Decimal 来避免浮点精度问题，并在写入 DB 前保证类型正确
    amount_decimal = Decimal(str(item.amount))

    db_salary = SalaryLog(
        amount=amount_decimal,
        
        # 【核心概念】
        # 刚入账时，这笔钱完全没被分配，所以"未使用金额"等于"总金额"。
        # 随着你调用 /settle 接口，这个字段会不断减少，直到变为 0。
        amount_unused=amount_decimal,
        source=item.source,
        remark=item.remark,
        month=item.month,
        received_date=actual_date,
        created_at=datetime.now(BEIJING_TZ)
    )

    try:
        db.add(db_salary)
        db.commit()
        return "成功保存回款记录"
    except Exception as e:
        db.rollback()
        # 抛出友好的 HTTP 错误，方便客户端和日志排查
        raise HTTPException(500, f"保存回款失败: {str(e)}")

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
            amount=settle_amount,
            created_at=datetime.now(BEIJING_TZ)
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

@app.put("/transactions/{transaction_id}", tags=["5. 更新账单"])
def update_transaction(transaction_id: int, item: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    """更新账单信息"""
    txn = db.query(Transaction).get(transaction_id)
    if not txn:
        raise HTTPException(404, "账单不存在")
    
    # 只允许更新标题和分类
    txn.title = item.title
    txn.amount_out = item.amount_out
    txn.category = item.category

    # 如果更新了 amount_out，需要重新计算状态
    rest = txn.amount_out - txn.amount_reimbursed
    if rest == 0:
        txn.status = TransactionStatus.settled
    if rest > 0:
        if txn.amount_reimbursed == 0:
            txn.status = TransactionStatus.pending
        else:
            txn.status = TransactionStatus.partially_settled
    if rest < 0:
        raise HTTPException(400, "更新后的垫付金额不能小于已还金额")
    
    try:
        db.commit()
        return "账单更新成功"
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"更新账单失败: {str(e)}")

@app.get("/summary", tags=["4. 监控大盘"])
def get_dashboard(db: Session = Depends(get_db)):
    """
    【债权人终极监控】
    不管父亲的钱是工资还是老板报销，也不管他私吞了没。
    只计算：我出了多少？回了多少？还差多少？
    """

    # --- A. 经营循环 (为了平账) ---
    business_lent = db.query(func.sum(Transaction.amount_out))\
        .filter(Transaction.category.in_(BUSINESS_CATEGORIES)).scalar() or Decimal("0")
    business_reimbursed = db.query(func.sum(SalaryLog.amount))\
        .filter(SalaryLog.source == IncomeSource.reimbursement).scalar() or Decimal("0")
    business_debt = business_lent - business_reimbursed

    # --- B. 生活循环 (为了存钱) ---
    salary_income = db.query(func.sum(SalaryLog.amount))\
        .filter(SalaryLog.source.in_(PERSONAL_INCOME_SOURCES)).scalar() or Decimal("0")
    personal_spending = db.query(func.sum(Transaction.amount_out))\
        .filter(Transaction.category == Category.personal).scalar() or Decimal("0")
    net_savings = salary_income - personal_spending

    # --- C. 资金池与核销进度 ---
    ledger_outstanding = db.query(
        func.sum(Transaction.amount_out - Transaction.amount_reimbursed)
    ).filter(Transaction.status != TransactionStatus.settled).scalar() or Decimal("0")
    wallet_unallocated = db.query(func.sum(SalaryLog.amount_unused)).scalar() or Decimal("0")

    salary_wallet, reimbursement_wallet = db.query(
        func.sum(case(
            (SalaryLog.source.in_(PERSONAL_INCOME_SOURCES), SalaryLog.amount_unused),
            else_=0
        )),
        func.sum(case(
            (SalaryLog.source == IncomeSource.reimbursement, SalaryLog.amount_unused),
            else_=0
        ))
    ).one()
    salary_wallet = salary_wallet or Decimal("0")
    reimbursement_wallet = reimbursement_wallet or Decimal("0")

    personal_unsettled, business_unsettled = db.query(
        func.sum(case(
            (Transaction.category == Category.personal, Transaction.amount_out - Transaction.amount_reimbursed),
            else_=0
        )),
        func.sum(case(
            (Transaction.category.in_(BUSINESS_CATEGORIES), Transaction.amount_out - Transaction.amount_reimbursed),
            else_=0
        ))
    ).filter(Transaction.status != TransactionStatus.settled).one()
    personal_unsettled = personal_unsettled or Decimal("0")
    business_unsettled = business_unsettled or Decimal("0")

    action_suggestions = []
    if personal_unsettled > Decimal("0") and salary_wallet > Decimal("0"):
        action_suggestions.append(ACTION_USE_SALARY_FOR_PERSONAL)
    if business_unsettled > Decimal("0") and reimbursement_wallet > Decimal("0"):
        action_suggestions.append(ACTION_USE_REIMBURSEMENT_FOR_BUSINESS)

    return {
        "financial_status": {
            "description": "经营循环 (为了平账)",
            "total_business_lent": float(business_lent),
            "total_reimbursed": float(business_reimbursed),
            "business_debt": float(business_debt),
            "status": "老板还欠我钱，请催报销。" if business_debt > 0 else "经营账已结清或有盈余。"
        },
        "life_status": {
            "description": "生活循环 (为了存钱)",
            "total_income": float(salary_income),
            "total_personal_spending": float(personal_spending),
            "net_savings": float(net_savings),
            "status": "净储蓄保持平衡或盈余，继续保持。" if net_savings >= 0 else "净储蓄为负，建议控制支出。"
        },
        "operational_status": {
            "description": "资金池与核销建议",
            "bills_pending_settlement": float(ledger_outstanding),
            "cash_waiting_allocation": float(wallet_unallocated),
            "salary_cash_available": float(salary_wallet),
            "reimbursement_cash_available": float(reimbursement_wallet),
            "action_needed": "; ".join(action_suggestions) if action_suggestions else "暂无操作"
        }
    }
