import unittest

from sqlalchemy.exc import ProgrammingError

from app.core.exceptions import AppError
from app.modules.trade_records.service import _handle_schema_error


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


if __name__ == "__main__":
    unittest.main()
