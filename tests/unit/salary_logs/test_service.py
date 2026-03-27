from datetime import datetime
from decimal import Decimal
import unittest

from app.domain.enums import IncomeSource
from app.modules.salary_logs.schemas import SalaryLogUpdate
from app.modules.salary_logs.service import update_salary_log


class DummySalaryLog:
    def __init__(self):
        self.id = 1
        self.amount = Decimal("100")
        self.amount_unused = Decimal("40")
        self.month = "2024-01"
        self.source = IncomeSource.salary
        self.remark = "原备注"
        self.received_date = datetime(2024, 1, 15)


class DummySession:
    def __init__(self, salary_log):
        self.salary_log = salary_log
        self.committed = False
        self.rolled_back = False
        self.refreshed = False

    def get(self, model, salary_log_id):
        if salary_log_id == self.salary_log.id:
            return self.salary_log
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, salary_log):
        self.refreshed = salary_log is self.salary_log


class SalaryLogServiceTests(unittest.TestCase):
    def test_update_salary_log_keeps_month_when_omitted(self):
        salary_log = DummySalaryLog()
        db = DummySession(salary_log)

        payload = SalaryLogUpdate(amount=Decimal("120"), source=IncomeSource.salary, remark="新备注")
        result = update_salary_log(db, 1, payload)

        self.assertTrue(db.committed)
        self.assertTrue(db.refreshed)
        self.assertEqual(result.month, "2024-01")
        self.assertEqual(result.remark, "新备注")
        self.assertEqual(result.amount_unused, Decimal("60"))


if __name__ == "__main__":
    unittest.main()
