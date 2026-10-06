from decimal import Decimal
import unittest
from unittest.mock import Mock
from app.core.exceptions import BusinessRuleError
from app.domain.enums import Category, TransactionStatus
from app.models import SalaryLog, Transaction
from app.modules.settlements.service import _apply_settlement


class ApplySettlementTests(unittest.TestCase):
    def records(self):
        return Transaction(
            category=Category.personal,
            amount_out=Decimal("40.05"),
            amount_reimbursed=Decimal("0"),
            status=TransactionStatus.pending,
        ), SalaryLog(amount=Decimal("100"), amount_unused=Decimal("100"))

    def test_changes_both_sides_and_derives_status_with_exact_cents(self):
        transaction, income = self.records()
        db = Mock()
        _apply_settlement(db, transaction, income, Decimal("40.05"))
        self.assertEqual(income.amount_unused, Decimal("59.95"))
        self.assertEqual(transaction.amount_reimbursed, Decimal("40.05"))
        self.assertEqual(transaction.status, TransactionStatus.settled)
        db.commit.assert_not_called()
        record = db.add.call_args.args[0]
        self.assertIs(record.transaction, transaction)
        self.assertIs(record.salary_log, income)

    def test_does_not_modify_either_side_when_income_or_debt_is_insufficient(self):
        for amount in ["50", "101"]:
            transaction, income = self.records()
            db = Mock()
            with self.assertRaises(BusinessRuleError):
                _apply_settlement(db, transaction, income, Decimal(amount))
            self.assertEqual(income.amount_unused, Decimal("100"))
            self.assertEqual(transaction.amount_reimbursed, Decimal("0"))
            db.add.assert_not_called()
