from collections import defaultdict

from sqlalchemy.orm import Session

from app.domain.enums import Category, IncomeSource
from app.modules.summary import queries



def build_chart_data(db: Session, month: str | None = None) -> dict:
    spending_rows = queries.get_monthly_spending_by_category(db, month=month)
    income_rows = queries.get_monthly_income_by_source(db, month=month)
    category_rows = queries.get_category_totals(db, month=month)

    months = defaultdict(
        lambda: {
            "month": "",
            "income_salary": 0,
            "income_reimbursement": 0,
            "spending_work": 0,
            "spending_personal": 0,
        }
    )

    for row in spending_rows:
        current = months[row.month]
        current["month"] = row.month
        if row.category == Category.work:
            current["spending_work"] = float(row.total)
        else:
            current["spending_personal"] = float(row.total)

    for row in income_rows:
        current = months[row.month]
        current["month"] = row.month
        if row.source == IncomeSource.salary:
            current["income_salary"] = float(row.total)
        elif row.source == IncomeSource.reimbursement:
            current["income_reimbursement"] = float(row.total)

    timeline = sorted(months.values(), key=lambda item: item["month"])
    category_breakdown = [
        {"name": "工作垫付" if row.category == Category.work else "个人消费", "value": float(row.total)}
        for row in category_rows
    ]

    return {
        "monthly_timeline": timeline,
        "category_breakdown": category_breakdown,
    }



def get_dashboard(db: Session, month: str | None = None) -> dict:
    total_personal_spending = queries.get_total_personal_spending(db, month=month)
    total_out = queries.get_total_out(db, month=month)
    total_business_lent = float(total_out) - float(total_personal_spending)

    total_reimbursed_from_boss = queries.get_total_income_by_source(
        db,
        IncomeSource.reimbursement,
        month=month,
    )
    total_salary_income = queries.get_total_income_by_source(db, IncomeSource.salary, month=month)

    real_business_debt = float(total_business_lent) - float(total_reimbursed_from_boss)
    net_family_savings = float(total_salary_income) - float(total_personal_spending)

    ledger_outstanding = queries.get_ledger_outstanding(db, month=month)
    wallet_unallocated = queries.get_wallet_unallocated(db, month=month)
    total_assets = float(wallet_unallocated) + float(ledger_outstanding)

    return {
        "chart_data": build_chart_data(db, month=month),
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
            "action_needed": "有闲钱，快去销账"
            if wallet_unallocated > 0 and ledger_outstanding > 0
            else "暂无操作",
        },
    }
