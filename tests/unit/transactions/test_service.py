from decimal import Decimal
import unittest

from app.domain.enums import Category, TransactionStatus
from app.modules.transactions.schemas import TransactionUpdate
from app.modules.transactions.service import calculate_transaction_status, update_transaction


class DummyTransaction:
    def __init__(self):
        self.id = 1
        self.title = "原始标题"
        self.amount_out = Decimal("100")
        self.amount_reimbursed = Decimal("20")
        self.category = Category.work
        self.status = TransactionStatus.partially_settled


class DummySession:
    def __init__(self, transaction):
        self.transaction = transaction
        self.committed = False
        self.rolled_back = False
        self.refreshed = False

    def get(self, model, transaction_id):
        if transaction_id == self.transaction.id:
            return self.transaction
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, transaction):
        self.refreshed = transaction is self.transaction


class TransactionServiceTests(unittest.TestCase):
    def test_calculate_transaction_status_boundaries(self):
        self.assertEqual(calculate_transaction_status(Decimal("100"), Decimal("0")), TransactionStatus.pending)
        self.assertEqual(
            calculate_transaction_status(Decimal("100"), Decimal("50")),
            TransactionStatus.partially_settled,
        )
        self.assertEqual(calculate_transaction_status(Decimal("100"), Decimal("100")), TransactionStatus.settled)

    def test_update_transaction_does_not_overwrite_missing_fields(self):
        transaction = DummyTransaction()
        db = DummySession(transaction)

        payload = TransactionUpdate(amount_out=120)
        result = update_transaction(db, 1, payload)

        self.assertTrue(db.committed)
        self.assertTrue(db.refreshed)
        self.assertEqual(result.title, "原始标题")
        self.assertEqual(result.category, Category.work)
        self.assertEqual(result.amount_out, Decimal("120"))
        self.assertEqual(result.status, TransactionStatus.partially_settled)


if __name__ == "__main__":
    unittest.main()
