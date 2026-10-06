import unittest
from decimal import Decimal
from app.domain.enums import TransactionStatus
from app.core.exceptions import BusinessRuleError
from app.modules.ledger.service import checksum_for, validate_snapshot
from tests.fixtures.ledger import snapshot


class LedgerValidationTests(unittest.TestCase):
    def test_detects_corrupted_file(self):
        data = snapshot()
        data.ledger.transactions[0].title = "已修改"
        with self.assertRaisesRegex(BusinessRuleError, "校验失败"):
            validate_snapshot(data)

    def test_detects_balance_or_missing_link_even_with_valid_checksum(self):
        for mutation in [
            lambda d: setattr(d.ledger.salary_logs[0], "amount_unused", Decimal("80")),
            lambda d: setattr(d.ledger.settlements[0], "transaction_id", 999),
            lambda d: setattr(
                d.ledger.transactions[0], "status", TransactionStatus.pending
            ),
        ]:
            data = snapshot()
            mutation(data)
            data.checksum = checksum_for(data.ledger)
            with self.assertRaises(BusinessRuleError):
                validate_snapshot(data)

    def test_detects_duplicate_ids_and_database_precision(self):
        data = snapshot()
        data.ledger.transactions.append(data.ledger.transactions[0])
        data.checksum = checksum_for(data.ledger)
        with self.assertRaisesRegex(BusinessRuleError, "重复"):
            validate_snapshot(data)
        data = snapshot()
        from decimal import Decimal

        data.ledger.trade_records[0].entry_price = Decimal("1.1234567")
        data.checksum = checksum_for(data.ledger)
        with self.assertRaisesRegex(BusinessRuleError, "精度"):
            validate_snapshot(data)
