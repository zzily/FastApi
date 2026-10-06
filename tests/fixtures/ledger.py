from app.modules.ledger.schemas import BackupSnapshot, LedgerData
from app.modules.ledger.service import checksum_for


def snapshot():
    ledger = LedgerData.model_validate(
        {
            "expense_categories": [
                {"id": 7, "name": "餐饮", "kind": "personal", "archived": False}
            ],
            "transactions": [
                {
                    "id": 20,
                    "title": "晚餐",
                    "category": "personal",
                    "amount_out": "20.05",
                    "amount_reimbursed": "20.05",
                    "status": "settled",
                    "receipt_url": "https://example.test/receipt",
                    "remark": "家庭聚餐",
                    "occurred_at": "2026-09-30",
                    "expense_category_id": 7,
                    "created_at": "2026-10-01T10:00:00",
                }
            ],
            "salary_logs": [
                {
                    "id": 30,
                    "amount": "100.00",
                    "amount_unused": "79.95",
                    "month": "2026-09",
                    "source": "salary",
                    "remark": "月薪",
                    "received_date": "2026-09-29T09:00:00",
                    "created_at": "2026-09-29T09:00:00",
                }
            ],
            "settlements": [
                {
                    "id": 40,
                    "transaction_id": 20,
                    "salary_log_id": 30,
                    "amount": "20.05",
                    "created_at": "2026-10-01T10:01:00",
                }
            ],
            "trade_records": [
                {
                    "id": 50,
                    "symbol": "TEST",
                    "market": "stock",
                    "side": "long",
                    "traded_at": "2026-09-28",
                    "pnl": "12.34",
                    "entry_price": "1.123456",
                    "fees": "0.05",
                    "mistake_tags": ["early_exit"],
                    "lesson": "遵守计划",
                    "note": "保留完整复盘",
                    "created_at": "2026-09-28T12:00:00",
                }
            ],
        }
    )
    return BackupSnapshot(
        exported_at="2026-10-01T12:00:00", ledger=ledger, checksum=checksum_for(ledger)
    )
