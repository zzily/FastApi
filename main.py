import logging
import time
from decimal import Decimal
from datetime import datetime
from typing import List

import pytz
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from sqlalchemy import create_engine, func, desc, select, extract
from sqlalchemy.orm import Session, sessionmaker

import schemas
from models import Transaction, TransactionStatus, Category, SalaryLog, TransactionSettlement

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Database config ---
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://4Azm2c71xKGJzVb.root:G8Ch4jZmQgOGeLKA@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/finance_manager?ssl_verify_cert=true&ssl_verify_identity=true"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

app = FastAPI(title="父亲财务监管系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BEIJING_TZ = pytz.timezone("Asia/Shanghai")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ok(message: str = "success", data=None) -> dict:
    """Unified success response"""
    return {"code": 200, "message": message, "data": data}


# --- Timing middleware ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info("%s %s - %.4fs", request.method, request.url.path, process_time)
    return response


# --- Chart data helper ---

def _build_chart_data(db: Session) -> dict:
    """Aggregate monthly income vs spending for charts."""

    # Monthly spending by category
    spending_rows = db.query(
        func.date_format(Transaction.created_at, "%Y-%m").label("month"),
        Transaction.category,
        func.sum(Transaction.amount_out).label("total"),
    ).group_by("month", Transaction.category).all()

    # Monthly income by source
    income_rows = db.query(
        SalaryLog.month,
        SalaryLog.source,
        func.sum(SalaryLog.amount).label("total"),
    ).group_by(SalaryLog.month, SalaryLog.source).all()

    # Merge into monthly timeline
    months: dict = defaultdict(lambda: {
        "month": "",
        "income_salary": 0,
        "income_reimbursement": 0,
        "spending_work": 0,
        "spending_personal": 0,
    })

    for row in spending_rows:
        m = months[row.month]
        m["month"] = row.month
        if row.category == Category.work:
            m["spending_work"] = float(row.total)
        else:
            m["spending_personal"] = float(row.total)

    for row in income_rows:
        m = months[row.month]
        m["month"] = row.month
        if row.source == "salary":
            m["income_salary"] = float(row.total)
        elif row.source == "reimbursement":
            m["income_reimbursement"] = float(row.total)

    timeline = sorted(months.values(), key=lambda x: x["month"])

    # Category breakdown (pie chart)
    category_rows = db.query(
        Transaction.category,
        func.sum(Transaction.amount_out).label("total"),
    ).group_by(Transaction.category).all()

    category_breakdown = [
        {"name": "工作垫付" if r.category == Category.work else "个人消费", "value": float(r.total)}
        for r in category_rows
    ]

    return {
        "monthly_timeline": timeline,
        "category_breakdown": category_breakdown,
    }


# --- Transaction endpoints ---

@app.get("/transactions/", response_model=List[schemas.TransactionRead], tags=["1. 记账 (债权)"])
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    unpaid_only: bool = False,
    db: Session = Depends(get_db),
):
    """获取账单列表"""
    query = db.query(Transaction)
    if unpaid_only:
        query = query.filter(Transaction.status != TransactionStatus.settled)
    return query.order_by(desc(Transaction.id)).offset(skip).limit(limit).all()


@app.post("/transactions/", tags=["1. 记账 (债权)"])
def create_transaction(item: schemas.TransactionCreate, db: Session = Depends(get_db)):
    """记录垫付"""
    db_txn = Transaction(
        title=item.title,
        amount_out=Decimal(str(item.amount_out)),
        category=item.category,
        created_at=datetime.now(BEIJING_TZ),
        amount_reimbursed=Decimal("0"),
        status=TransactionStatus.pending,
    )
    try:
        db.add(db_txn)
        db.commit()
        db.refresh(db_txn)
        return ok("成功保存账单", {"id": db_txn.id})
    except Exception as e:
        db.rollback()
        logger.error("保存账单失败: %s", e)
        raise HTTPException(500, f"保存账单失败: {e}")


@app.put("/transactions/{transaction_id}", tags=["5. 更新账单"])
def update_transaction(transaction_id: int, item: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    """更新账单信息"""
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(404, "账单不存在")

    txn.title = item.title
    txn.amount_out = item.amount_out
    txn.category = item.category

    rest = txn.amount_out - txn.amount_reimbursed
    if rest < 0:
        raise HTTPException(400, "更新后的垫付金额不能小于已还金额")
    if rest == 0:
        txn.status = TransactionStatus.settled
    elif txn.amount_reimbursed == 0:
        txn.status = TransactionStatus.pending
    else:
        txn.status = TransactionStatus.partially_settled

    try:
        db.commit()
        return ok("账单更新成功")
    except Exception as e:
        db.rollback()
        logger.error("更新账单失败: %s", e)
        raise HTTPException(500, f"更新账单失败: {e}")


@app.delete("/transactions/{transaction_id}", tags=["5. 删除账单"])
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """删除账单（有核销记录时禁止删除）"""
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(404, "账单不存在")

    # Check for linked settlement records
    settlement_count = db.query(func.count(TransactionSettlement.id)).filter(
        TransactionSettlement.transaction_id == transaction_id
    ).scalar()
    if settlement_count > 0:
        raise HTTPException(
            400,
            f"该账单已有 {settlement_count} 条核销记录，无法直接删除。请先撤销相关核销。",
        )

    try:
        db.delete(txn)
        db.commit()
        return ok("账单删除成功")
    except Exception as e:
        db.rollback()
        logger.error("删除账单失败: %s", e)
        raise HTTPException(500, f"删除账单失败: {e}")


# --- Salary log endpoints ---

@app.get("/salary_logs/", response_model=List[schemas.SalaryLogRead], tags=["2. 入账 (资金池)"])
def read_salary_logs(
    skip: int = 0,
    limit: int = 100,
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    """获取资金池记录"""
    query = db.query(SalaryLog)
    if available_only:
        query = query.filter(SalaryLog.amount_unused > 0)
    logs = query.order_by(desc(SalaryLog.id)).offset(skip).limit(limit).all()
    return [log for log in logs if log is not None]


@app.post("/salary_logs/", tags=["2. 入账 (资金池)"])
def create_salary_log(item: schemas.SalaryLogCreate, db: Session = Depends(get_db)):
    """记录回款入池"""
    actual_date = item.received_date if item.received_date else datetime.now(BEIJING_TZ)
    amount_decimal = Decimal(str(item.amount))

    db_salary = SalaryLog(
        amount=amount_decimal,
        amount_unused=amount_decimal,
        source=item.source,
        remark=item.remark,
        month=item.month,
        received_date=actual_date,
        created_at=datetime.now(BEIJING_TZ),
    )
    try:
        db.add(db_salary)
        db.commit()
        db.refresh(db_salary)
        return ok("成功保存回款记录", {"id": db_salary.id})
    except Exception as e:
        db.rollback()
        logger.error("保存回款失败: %s", e)
        raise HTTPException(500, f"保存回款失败: {e}")


@app.put("/salary_logs/{salary_log_id}", response_model=schemas.SalaryLogRead, tags=["2. 入账 (资金池)"])
def update_salary_log(salary_log_id: int, item: schemas.SalaryLogUpdate, db: Session = Depends(get_db)):
    """更新入账记录"""
    log = db.get(SalaryLog, salary_log_id)
    if not log:
        raise HTTPException(404, "记录不存在")

    amount_used = log.amount - log.amount_unused
    if item.amount < amount_used:
        raise HTTPException(400, f"金额修改失败！该笔资金已核销使用了 {amount_used} 元，新金额不能低于此数值。")

    log.source = item.source
    log.remark = item.remark
    log.month = item.month
    if item.received_date:
        log.received_date = item.received_date
    log.amount = item.amount
    log.amount_unused = item.amount - amount_used

    try:
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        logger.error("更新回款失败: %s", e)
        raise HTTPException(500, f"更新失败: {e}")


# --- Settlement endpoint ---

@app.post("/settle", tags=["3. 核销 (还钱)"])
def settle_debt(item: schemas.SettleRequest, db: Session = Depends(get_db)):
    """用回款核销账单"""
    txn = db.execute(
        select(Transaction).where(Transaction.id == item.transaction_id).with_for_update()
    ).scalar_one_or_none()
    salary = db.execute(
        select(SalaryLog).where(SalaryLog.id == item.salary_log_id).with_for_update()
    ).scalar_one_or_none()

    if not txn:
        raise HTTPException(404, "账单不存在")
    if not salary:
        raise HTTPException(404, "回款记录不存在")

    settle_amount = Decimal(str(item.amount))

    if salary.amount_unused < settle_amount:
        raise HTTPException(400, f"资金不足！该笔回款仅剩 {salary.amount_unused} 元，无法核销 {settle_amount} 元")

    remaining_debt = txn.amount_out - txn.amount_reimbursed
    if remaining_debt < settle_amount:
        raise HTTPException(400, f"超额核销！该账单仅欠 {remaining_debt} 元")

    try:
        salary.amount_unused -= settle_amount
        txn.amount_reimbursed += settle_amount

        if txn.amount_out - txn.amount_reimbursed == 0:
            txn.status = TransactionStatus.settled
        else:
            txn.status = TransactionStatus.partially_settled

        settlement_log = TransactionSettlement(
            transaction_id=txn.id,
            salary_log_id=salary.id,
            amount=settle_amount,
            created_at=datetime.now(BEIJING_TZ),
        )
        db.add(settlement_log)
        db.commit()

        return ok("核销成功", {
            "transaction_status": txn.status,
            "salary_remaining": float(salary.amount_unused),
            "transaction_remaining_debt": float(txn.amount_out - txn.amount_reimbursed),
        })
    except Exception as e:
        db.rollback()
        logger.error("核销失败: %s", e)
        raise HTTPException(500, f"核销失败: {e}")


# --- Settlement history & undo ---

@app.get("/transactions/{transaction_id}/settlements", tags=["3. 核销 (还钱)"])
def get_transaction_settlements(transaction_id: int, db: Session = Depends(get_db)):
    """获取某账单的核销历史明细"""
    txn = db.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(404, "账单不存在")

    records = (
        db.query(TransactionSettlement)
        .filter(TransactionSettlement.transaction_id == transaction_id)
        .order_by(desc(TransactionSettlement.created_at))
        .all()
    )

    result = []
    for r in records:
        salary = db.get(SalaryLog, r.salary_log_id)
        result.append({
            "id": r.id,
            "transaction_id": r.transaction_id,
            "salary_log_id": r.salary_log_id,
            "amount": float(r.amount),
            "salary_month": salary.month if salary else "未知",
            "salary_source": salary.source if salary else "other",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return ok("获取成功", result)


@app.delete("/settlements/{settlement_id}", tags=["3. 核销 (还钱)"])
def undo_settlement(settlement_id: int, db: Session = Depends(get_db)):
    """撤销一条核销记录，恢复资金池余额和账单状态"""
    record = db.get(TransactionSettlement, settlement_id)
    if not record:
        raise HTTPException(404, "核销记录不存在")

    txn = db.execute(
        select(Transaction).where(Transaction.id == record.transaction_id).with_for_update()
    ).scalar_one_or_none()
    salary = db.execute(
        select(SalaryLog).where(SalaryLog.id == record.salary_log_id).with_for_update()
    ).scalar_one_or_none()

    if not txn:
        raise HTTPException(404, "关联账单不存在")
    if not salary:
        raise HTTPException(404, "关联回款记录不存在")

    try:
        # Reverse the settlement
        txn.amount_reimbursed -= record.amount
        salary.amount_unused += record.amount

        # Recalculate transaction status
        if txn.amount_reimbursed <= 0:
            txn.amount_reimbursed = Decimal("0")
            txn.status = TransactionStatus.pending
        elif txn.amount_reimbursed < txn.amount_out:
            txn.status = TransactionStatus.partially_settled
        else:
            txn.status = TransactionStatus.settled

        db.delete(record)
        db.commit()

        return ok("撤销成功", {
            "transaction_status": txn.status,
            "transaction_remaining_debt": float(txn.amount_out - txn.amount_reimbursed),
            "salary_remaining": float(salary.amount_unused),
        })
    except Exception as e:
        db.rollback()
        logger.error("撤销核销失败: %s", e)
        raise HTTPException(500, f"撤销核销失败: {e}")


# --- Dashboard endpoint ---

@app.get("/summary", tags=["4. 监控大盘"])
def get_dashboard(db: Session = Depends(get_db)):
    """获取财务大盘数据"""

    # Spending breakdown
    total_personal_spending = db.query(func.sum(Transaction.amount_out)).filter(
        Transaction.category == Category.personal
    ).scalar() or 0

    total_out = db.query(func.sum(Transaction.amount_out)).scalar() or 0
    total_business_lent = float(total_out) - float(total_personal_spending)

    # Income breakdown
    total_reimbursed_from_boss = db.query(func.sum(SalaryLog.amount)).filter(
        SalaryLog.source == "reimbursement"
    ).scalar() or 0

    total_salary_income = db.query(func.sum(SalaryLog.amount)).filter(
        SalaryLog.source == "salary"
    ).scalar() or 0

    # Core metrics
    real_business_debt = float(total_business_lent) - float(total_reimbursed_from_boss)
    net_family_savings = float(total_salary_income) - float(total_personal_spending)

    # Asset overview
    ledger_outstanding = db.query(
        func.sum(Transaction.amount_out - Transaction.amount_reimbursed)
    ).scalar() or 0
    wallet_unallocated = db.query(func.sum(SalaryLog.amount_unused)).scalar() or 0
    total_assets = float(wallet_unallocated) + float(ledger_outstanding)

    return ok("获取成功", {
        "chart_data": _build_chart_data(db),
        "financial_status": {
            "description": "家庭财务双循环",
            "business_loop": {
                "total_lent": float(total_business_lent),
                "total_reimbursed": float(total_reimbursed_from_boss),
                "current_debt": real_business_debt,
                "status": "等待报销" if real_business_debt > 0 else "已平账",
            },
            "family_loop": {
                "gross_income": float(total_salary_income),
                "personal_spending": float(total_personal_spending),
                "net_savings": net_family_savings,
                "status": "资产增值中" if net_family_savings > 0 else "入不敷出",
            },
            "total_assets": total_assets,
        },
        "operational_status": {
            "description": "操作概览",
            "bills_pending_settlement": float(ledger_outstanding),
            "cash_waiting_allocation": float(wallet_unallocated),
            "action_needed": "有闲钱，快去销账" if wallet_unallocated > 0 and ledger_outstanding > 0 else "暂无操作",
        },
    })
