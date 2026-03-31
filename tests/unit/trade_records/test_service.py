from datetime import date, datetime
from decimal import Decimal
import unittest

from sqlalchemy.exc import ProgrammingError

from app.core.exceptions import AppError, BusinessRuleError
from app.domain.enums import (
    TradeExecutionQuality,
    TradeMarket,
    TradePlanClarity,
    TradeSide,
)
from app.modules.trade_records.schemas import TradeRecordUpdate
from app.modules.trade_records.service import _handle_schema_error, update_trade_record


class DummyTradeRecord:
    def __init__(self):
        self.id = 1
        self.symbol = "BTCUSDT"
        self.market = TradeMarket.crypto
        self.side = TradeSide.long
        self.traded_at = date(2026, 3, 31)
        self.pnl = Decimal("320.5")
        self.setup = "趋势突破"
        self.note = "原始备注"
        self.entry_at = datetime(2026, 3, 31, 9, 30)
        self.exit_at = datetime(2026, 3, 31, 10, 30)
        self.entry_price = Decimal("88000")
        self.exit_price = Decimal("88320")
        self.position_size = Decimal("1")
        self.thesis = "突破后延续"
        self.planned_stop = Decimal("87800")
        self.planned_target = Decimal("88500")
        self.actual_stop = None
        self.actual_target = Decimal("88320")
        self.fees = Decimal("12")
        self.slippage = Decimal("3")
        self.followed_plan = True
        self.plan_clarity = TradePlanClarity.clear
        self.execution_quality = TradeExecutionQuality.disciplined
        self.mistake_tags = []
        self.lesson = "原始结论"
        self.option_expiration = None
        self.option_strike = None
        self.option_right = None
        self.option_structure = None
        self.option_premium_type = None
        self.option_max_risk = None
        self.option_max_reward = None
        self.option_delta = None


class DummySession:
    def __init__(self, trade_record):
        self.trade_record = trade_record
        self.committed = False
        self.rolled_back = False
        self.refreshed = False

    def get(self, model, trade_record_id):
        if trade_record_id == self.trade_record.id:
            return self.trade_record
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, trade_record):
        self.refreshed = trade_record is self.trade_record


class TradeRecordServiceTests(unittest.TestCase):
    def test_handle_schema_error_returns_actionable_message_for_missing_table(self):
        error = ProgrammingError(
            "SELECT * FROM trade_records",
            {},
            Exception("Table 'finance_manager.trade_records' doesn't exist"),
        )

        with self.assertRaises(AppError) as context:
            _handle_schema_error(error)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(
            context.exception.message,
            "交易日志数据表尚未初始化，请先执行数据库迁移（alembic upgrade head）。",
        )

    def test_update_trade_record_does_not_overwrite_missing_fields(self):
        trade_record = DummyTradeRecord()
        db = DummySession(trade_record)

        payload = TradeRecordUpdate(pnl=Decimal("410.25"), lesson="只做 A 级 setup")
        result = update_trade_record(db, 1, payload)

        self.assertTrue(db.committed)
        self.assertTrue(db.refreshed)
        self.assertEqual(result.symbol, "BTCUSDT")
        self.assertEqual(result.pnl, Decimal("410.25"))
        self.assertEqual(result.setup, "趋势突破")
        self.assertEqual(result.lesson, "只做 A 级 setup")
        self.assertEqual(result.plan_clarity, TradePlanClarity.clear)

    def test_update_trade_record_can_clear_optional_fields(self):
        trade_record = DummyTradeRecord()
        db = DummySession(trade_record)

        payload = TradeRecordUpdate(
            setup=None,
            note=None,
            thesis=None,
            mistake_tags=[],
            followed_plan=None,
            plan_clarity=None,
            execution_quality=None,
            lesson=None,
        )
        result = update_trade_record(db, 1, payload)

        self.assertIsNone(result.setup)
        self.assertIsNone(result.note)
        self.assertIsNone(result.thesis)
        self.assertEqual(result.mistake_tags, [])
        self.assertIsNone(result.followed_plan)
        self.assertIsNone(result.plan_clarity)
        self.assertIsNone(result.execution_quality)
        self.assertIsNone(result.lesson)

    def test_update_trade_record_rejects_invalid_time_range(self):
        trade_record = DummyTradeRecord()
        db = DummySession(trade_record)

        payload = TradeRecordUpdate(
            entry_at=datetime(2026, 3, 31, 11, 0),
            exit_at=datetime(2026, 3, 31, 10, 0),
        )

        with self.assertRaises(BusinessRuleError) as context:
            update_trade_record(db, 1, payload)

        self.assertEqual(context.exception.message, "出场时间需要晚于入场时间")
        self.assertFalse(db.committed)


if __name__ == "__main__":
    unittest.main()
