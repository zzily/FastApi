from fastapi import APIRouter

from app.modules.salary_logs.router import router as salary_logs_router
from app.modules.settlements.router import router as settlements_router
from app.modules.summary.router import router as summary_router
from app.modules.trade_records.router import router as trade_records_router
from app.modules.transactions.router import router as transactions_router

api_router = APIRouter()
api_router.include_router(transactions_router)
api_router.include_router(salary_logs_router)
api_router.include_router(settlements_router)
api_router.include_router(summary_router)
api_router.include_router(trade_records_router)
